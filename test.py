import streamlit as st
import os
import csv
from filelock import FileLock, Timeout

st.title("🎧 本地音频水印对比评分系统")

# === 用户输入主文件夹路径 ===
base_dir = st.text_input("请输入包含 original 和各水印方法文件夹的主目录路径：", "")
start_button = st.button("加载音频数据")

# === 初始化状态 ===
if "idx" not in st.session_state:
    st.session_state.idx = 0
    st.session_state.results = []
    st.session_state.audio_files = []
    st.session_state.method_dirs = []

# === 加载逻辑 ===
if start_button and os.path.isdir(base_dir):
    original_dir = os.path.join(base_dir, "original")
    if not os.path.isdir(original_dir):
        st.error("❌ 没有找到 'original' 文件夹，请确认路径正确。")
    else:
        audio_files = sorted(f for f in os.listdir(original_dir) if f.endswith(".wav") or f.endswith(".flac"))
        method_dirs = sorted([
            d for d in os.listdir(base_dir)
            if os.path.isdir(os.path.join(base_dir, d)) and d != "original"
        ])
        st.session_state.audio_files = audio_files
        st.session_state.method_dirs = method_dirs
        st.session_state.base_dir = base_dir
        st.session_state.original_dir = original_dir
        st.session_state.idx = 0
        st.session_state.results = []
        st.success(f"成功加载 {len(audio_files)} 个音频文件，{len(method_dirs)} 种水印方法。")

# === 主流程逻辑 ===
audio_files = st.session_state.get("audio_files", [])
method_dirs = st.session_state.get("method_dirs", [])
base_dir = st.session_state.get("base_dir", "")
original_dir = st.session_state.get("original_dir", "")
total = len(audio_files)
cur_idx = st.session_state.idx

if audio_files and cur_idx >= total:
    st.success("✅ 所有音频对已评估完成！感谢参与！")

    result_file = os.path.join(base_dir, "results.csv")
    lock_file = result_file + ".lock"

    if st.session_state.results:
        try:
            with FileLock(lock_file, timeout=10):
                file_exists = os.path.exists(result_file)
                with open(result_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    if not file_exists:
                        writer.writerow(["filename", "method", "rating"])
                    writer.writerows(st.session_state.results)
                st.session_state.results.clear()
        except Timeout:
            st.warning("⚠️ 当前有其他用户正在提交，请稍后再试")
    st.stop()

if audio_files and cur_idx < total:
    cur_file = audio_files[cur_idx]
    st.subheader(f"🧪 正在评估第 {cur_idx + 1}/{total} 个音频文件： `{cur_file}`")

    st.audio(os.path.join(original_dir, cur_file))
    st.caption("🎧 原始音频")

    ratings = {}

    # 遍历每个水印方法并展示对比播放器和评分
    for method in method_dirs:
        wm_path = os.path.join(base_dir, method, cur_file)
        if os.path.exists(wm_path):
            st.markdown(f"**📌 方法：{method}**")
            st.audio(wm_path)
            rating = st.radio(
                f"你觉得 `{method}` 方法与原始音频的差异如何？",
                ["1-完全一致", "2-几乎一致", "3-轻微差异", "4-明显差异", "5-非常不同"],
                key=f"{cur_file}_{method}"
            )
            ratings[method] = rating
        else:
            st.warning(f"⚠️ `{method}` 方法下缺少 `{cur_file}`，跳过展示。")

    if st.button("提交并进入下一组"):
        for method, rating in ratings.items():
            st.session_state.results.append([cur_file, method, rating])
        st.session_state.idx += 1
        st.experimental_rerun()
