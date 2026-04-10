#!/bin/bash
# OpenCV 4.13.0 下载脚本（带重试机制）

echo "=========================================="
echo "OpenCV 4.13.0 下载（带重试）"
echo "=========================================="
echo ""

cd ~

# 下载函数，带重试
download_with_retry() {
    local url=$1
    local filename=$2
    local max_retries=3
    local retry=0

    while [ $retry -lt $max_retries ]; do
        echo "[尝试 $((retry+1)/$max_retries)] 下载 $filename..."

        if [ -f "$filename" ]; then
            rm -f "$filename"
        fi

        if curl -L -o "$filename" "$url" --retry 3 --retry-delay 5; then
            # 验证文件
            if [ -s "$filename" ]; then
                SIZE=$(stat -f%z "$filename" 2>/dev/null || stat -c%s "$filename" 2>/dev/null)
                echo "✓ 下载完成: $(du -h "$filename" | cut -f1)"

                # 验证zip文件
                if unzip -t "$filename" 2>/dev/null; then
                    echo "✓ 文件验证通过"
                    return 0
                else
                    echo "✗ 文件损坏，删除并重试..."
                    rm -f "$filename"
                fi
            else
                echo "✗ 下载失败，文件为空"
            fi
        else
            echo "✗ curl下载失败"
        fi

        retry=$((retry+1))
        sleep 2
    done

    echo "✗ 下载失败，已达到最大重试次数"
    return 1
}

# 下载OpenCV主仓库
echo "=== 下载OpenCV主仓库 ==="
if [ -d "opencv" ]; then
    echo "⚠ opencv目录已存在，跳过下载"
else
    if download_with_retry "https://codeload.github.com/opencv/opencv/zip/refs/tags/4.13.0" "opencv.zip"; then
        echo "解压opencv.zip..."
        unzip -q opencv.zip
        mv opencv-4.13.0 opencv
        rm opencv.zip
        echo "✓ OpenCV主仓库下载完成"
    else
        echo "✗ OpenCV主仓库下载失败"
        exit 1
    fi
fi
echo ""

# 下载OpenCV contrib
echo "=== 下载OpenCV contrib ==="
if [ -d "opencv_contrib" ]; then
    echo "⚠ opencv_contrib目录已存在，跳过下载"
else
    if download_with_retry "https://codeload.github.com/opencv/opencv_contrib/zip/refs/tags/4.13.0" "opencv_contrib.zip"; then
        echo "解压opencv_contrib.zip..."
        unzip -q opencv_contrib.zip
        mv opencv_contrib-4.13.0 opencv_contrib
        rm opencv_contrib.zip
        echo "✓ OpenCV contrib下载完成"
    else
        echo "✗ OpenCV contrib下载失败"
        exit 1
    fi
fi
echo ""

echo "=========================================="
echo "下载完成！"
echo "=========================================="
echo ""
echo "目录:"
ls -ld opencv opencv_contrib
echo ""
echo "文件大小:"
du -sh opencv opencv_contrib