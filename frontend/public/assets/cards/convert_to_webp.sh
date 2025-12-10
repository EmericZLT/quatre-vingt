#!/bin/bash

# 批量将 PNG 转换为 WebP
# 使用方法: ./convert_to_webp.sh

# 设置质量参数（80 是推荐值，在体积和质量之间取得平衡）
QUALITY=80

# 计数器
count=0
success=0
failed=0

echo "开始转换 PNG 到 WebP (质量: $QUALITY)..."
echo ""

# 遍历所有 PNG 文件
for png_file in *.png; do
    # 检查文件是否存在（避免通配符没有匹配到文件的情况）
    if [ ! -f "$png_file" ]; then
        continue
    fi
    
    # 生成 WebP 文件名
    webp_file="${png_file%.png}.webp"
    
    # 转换
    echo "转换: $png_file -> $webp_file"
    if cwebp -q $QUALITY "$png_file" -o "$webp_file" 2>/dev/null; then
        success=$((success + 1))
        echo "  ✓ 成功"
    else
        failed=$((failed + 1))
        echo "  ✗ 失败"
    fi
    
    count=$((count + 1))
done

echo ""
echo "转换完成！"
echo "总计: $count 个文件"
echo "成功: $success 个"
echo "失败: $failed 个"

