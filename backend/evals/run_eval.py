"""
DramaInsight 评测脚本
用法：python run_eval.py
"""
import os
import json
from pathlib import Path

EVAL_DIR = Path(__file__).parent
DATASET_DIR = EVAL_DIR / "dataset"


def load_dataset():
    """加载评测数据集"""
    dataset = []
    for file in DATASET_DIR.glob("*.json"):
        with open(file, "r", encoding="utf-8") as f:
            dataset.append(json.load(f))
    return dataset


def calc_scene_accuracy(predictions, ground_truth, time_tolerance=5.0):
    """计算剧情节点准确率：类型匹配且时间差在容忍范围内算正确"""
    correct = 0
    total = len(ground_truth)
    for gt in ground_truth:
        for pred in predictions:
            if pred["type"] == gt["type"]:
                if abs(pred["start_time"] - gt["start_time"]) <= time_tolerance:
                    correct += 1
                    break
    return correct / total if total > 0 else 0


def calc_meme_accuracy(predictions, ground_truth, time_tolerance=5.0):
    """计算名场面准确率"""
    correct = 0
    total = len(ground_truth)
    for gt in ground_truth:
        for pred in predictions:
            if pred["type"] == gt["type"]:
                if abs(pred["start_time"] - gt["start_time"]) <= time_tolerance:
                    correct += 1
                    break
    return correct / total if total > 0 else 0


def main():
    dataset = load_dataset()
    if not dataset:
        print("评测数据集为空，请先在 dataset/ 目录添加标注文件")
        return

    print(f"加载评测集：{len(dataset)} 条")
    print("=" * 50)

    scene_accs = []
    meme_accs = []

    for item in dataset:
        name = item.get("name", "unnamed")
        # 这里应该调用真实分析接口，MVP版本用模拟数据
        # predictions = analyze_video(item["video_path"])

        # 模拟评测结果（替换为真实调用）
        print(f"分析: {name}")
        # scene_acc = calc_scene_accuracy(predictions["scenes"], item["scenes"])
        # meme_acc = calc_meme_accuracy(predictions["memes"], item["memes"])
        # scene_accs.append(scene_acc)
        # meme_accs.append(meme_acc)
        print(f"  （待接入真实分析接口）")

    print("=" * 50)
    print("评测报告（待接入真实数据）")
    print(f"  剧情节点准确率: 待测")
    print(f"  名场面准确率: 待测")


if __name__ == "__main__":
    main()
