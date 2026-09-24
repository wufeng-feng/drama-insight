"""DramaInsight 离线/接口评测工具。"""

import argparse
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import httpx

EVAL_DIR = Path(__file__).parent
DATASET_DIR = EVAL_DIR / "dataset"


@dataclass
class MetricCounts:
    true_positive: int = 0
    false_positive: int = 0
    false_negative: int = 0

    def add(self, other: "MetricCounts") -> None:
        self.true_positive += other.true_positive
        self.false_positive += other.false_positive
        self.false_negative += other.false_negative

    @property
    def precision(self) -> float:
        denominator = self.true_positive + self.false_positive
        return self.true_positive / denominator if denominator else 0.0

    @property
    def recall(self) -> float:
        denominator = self.true_positive + self.false_negative
        return self.true_positive / denominator if denominator else 0.0

    @property
    def f1(self) -> float:
        denominator = self.precision + self.recall
        return 2 * self.precision * self.recall / denominator if denominator else 0.0


def load_dataset(dataset_dir: Path = DATASET_DIR) -> List[Dict]:
    dataset = []
    for file_path in sorted(dataset_dir.glob("*.json")):
        with file_path.open("r", encoding="utf-8") as source:
            item = json.load(source)
        item["_source_file"] = str(file_path)
        dataset.append(item)
    return dataset


def match_events(
    predictions: Iterable[Dict],
    ground_truth: Iterable[Dict],
    time_tolerance: float = 5.0,
) -> MetricCounts:
    """按类型和起始时间做一对一匹配，避免一个预测重复命中多条标注。"""
    predictions = list(predictions)
    ground_truth = list(ground_truth)
    candidates: List[Tuple[float, int, int]] = []

    for prediction_index, prediction in enumerate(predictions):
        for truth_index, truth in enumerate(ground_truth):
            if prediction.get("type") != truth.get("type"):
                continue
            time_error = abs(
                float(prediction.get("start_time", 0))
                - float(truth.get("start_time", 0))
            )
            if time_error <= time_tolerance:
                candidates.append((time_error, prediction_index, truth_index))

    matched_predictions = set()
    matched_truth = set()
    for _, prediction_index, truth_index in sorted(candidates):
        if prediction_index in matched_predictions or truth_index in matched_truth:
            continue
        matched_predictions.add(prediction_index)
        matched_truth.add(truth_index)

    true_positive = len(matched_predictions)
    return MetricCounts(
        true_positive=true_positive,
        false_positive=len(predictions) - true_positive,
        false_negative=len(ground_truth) - true_positive,
    )


def analyze_via_api(
    api_url: str,
    video_path: Path,
    timeout_seconds: float,
) -> Dict:
    base_url = api_url.rstrip("/")
    deadline = time.monotonic() + timeout_seconds

    with httpx.Client(timeout=60.0) as client:
        with video_path.open("rb") as video_file:
            response = client.post(
                f"{base_url}/api/analyze",
                files={"file": (video_path.name, video_file)},
            )
        response.raise_for_status()
        task_id = response.json()["task_id"]

        while time.monotonic() < deadline:
            task_response = client.get(f"{base_url}/api/analyze/{task_id}")
            task_response.raise_for_status()
            task = task_response.json()
            if task["status"] == "completed":
                return task["result"]
            if task["status"] == "failed":
                raise RuntimeError(task.get("error") or "分析任务失败")
            time.sleep(2)

    raise TimeoutError(f"分析任务超过 {timeout_seconds:.0f} 秒")


def resolve_prediction(
    item: Dict,
    api_url: str | None,
    timeout_seconds: float,
) -> Dict | None:
    embedded_prediction = item.get("prediction")
    if embedded_prediction:
        return embedded_prediction

    video_path_value = item.get("video_path")
    if not api_url or not video_path_value:
        return None

    source_file = Path(item["_source_file"])
    video_path = (source_file.parent / video_path_value).resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"找不到评测视频：{video_path}")
    return analyze_via_api(api_url, video_path, timeout_seconds)


def print_metrics(label: str, counts: MetricCounts) -> None:
    print(
        f"{label}: Precision={counts.precision:.3f} "
        f"Recall={counts.recall:.3f} F1={counts.f1:.3f} "
        f"(TP={counts.true_positive}, FP={counts.false_positive}, "
        f"FN={counts.false_negative})"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="DramaInsight 评测工具")
    parser.add_argument(
        "--api-url",
        help="可选，例如 http://localhost:8000；提供后会上传含 video_path 的样本",
    )
    parser.add_argument("--time-tolerance", type=float, default=5.0)
    parser.add_argument("--timeout", type=float, default=180.0)
    arguments = parser.parse_args()

    dataset = load_dataset()
    if not dataset:
        print("评测集为空，请在 evals/dataset 中添加标注 JSON")
        return 0

    scene_total = MetricCounts()
    meme_total = MetricCounts()
    evaluated = 0

    print(f"加载评测集：{len(dataset)} 条")
    print("=" * 64)

    for item in dataset:
        name = item.get("name", "unnamed")
        try:
            prediction = resolve_prediction(
                item,
                arguments.api_url,
                arguments.timeout,
            )
        except Exception as exc:
            print(f"[失败] {name}: {exc}")
            continue

        if prediction is None:
            print(f"[跳过] {name}: 缺少 prediction，且未同时提供 --api-url 和 video_path")
            continue

        scene_counts = match_events(
            prediction.get("scenes", []),
            item.get("scenes", []),
            arguments.time_tolerance,
        )
        meme_counts = match_events(
            prediction.get("memes", []),
            item.get("memes", []),
            arguments.time_tolerance,
        )
        scene_total.add(scene_counts)
        meme_total.add(meme_counts)
        evaluated += 1

        print(f"[完成] {name}")
        print_metrics("  剧情节点", scene_counts)
        print_metrics("  高光片段", meme_counts)

    print("=" * 64)
    if evaluated == 0:
        print("没有可评测样本，因此不会生成虚假的准确率。")
        return 0

    print(f"有效样本：{evaluated}")
    print_metrics("剧情节点总计", scene_total)
    print_metrics("高光片段总计", meme_total)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
