#!/bin/bash

# 测试框架验证脚本
# 用于快速验证测试框架是否正确配置

echo "=================================================="
echo "  前端测试框架验证"
echo "=================================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 Node.js 和 npm
echo -e "${YELLOW}1. 检查 Node.js 和 npm...${NC}"
if command -v node &> /dev/null; then
    echo -e "${GREEN}✓ Node.js: $(node --version)${NC}"
else
    echo -e "${RED}✗ Node.js 未安装${NC}"
    exit 1
fi

if command -v npm &> /dev/null; then
    echo -e "${GREEN}✓ npm: $(npm --version)${NC}"
else
    echo -e "${RED}✗ npm 未安装${NC}"
    exit 1
fi

echo ""

# 检查依赖
echo -e "${YELLOW}2. 检查测试依赖...${NC}"
REQUIRED_DEPS=("jest" "@testing-library/react" "@testing-library/jest-dom" "@testing-library/user-event")
ALL_DEPS_OK=true

for dep in "${REQUIRED_DEPS[@]}"; do
    if npm list "$dep" &> /dev/null; then
        echo -e "${GREEN}✓ $dep${NC}"
    else
        echo -e "${RED}✗ $dep 未安装${NC}"
        ALL_DEPS_OK=false
    fi
done

if [ "$ALL_DEPS_OK" = false ]; then
    echo -e "${RED}请运行 npm install 安装依赖${NC}"
    exit 1
fi

echo ""

# 检查配置文件
echo -e "${YELLOW}3. 检查配置文件...${NC}"
CONFIG_FILES=("jest.config.js" "tests/setup.ts" "tests/test-utils.tsx")
ALL_FILES_OK=true

for file in "${CONFIG_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ $file${NC}"
    else
        echo -e "${RED}✗ $file 不存在${NC}"
        ALL_FILES_OK=false
    fi
done

if [ "$ALL_FILES_OK" = false ]; then
    echo -e "${RED}配置文件缺失，请检查${NC}"
    exit 1
fi

echo ""

# 运行框架验证测试
echo -e "${YELLOW}4. 运行框架验证测试...${NC}"
if npm test -- __tests__/setup.test.ts --silent; then
    echo -e "${GREEN}✓ 框架验证测试通过${NC}"
else
    echo -e "${RED}✗ 框架验证测试失败${NC}"
    exit 1
fi

echo ""

# 运行示例测试
echo -e "${YELLOW}5. 运行示例测试...${NC}"
if npm test -- __tests__/example/ --silent; then
    echo -e "${GREEN}✓ 示例测试通过${NC}"
else
    echo -e "${RED}✗ 示例测试失败${NC}"
    exit 1
fi

echo ""
echo "=================================================="
echo -e "${GREEN}  测试框架验证成功！ ✓${NC}"
echo "=================================================="
echo ""
echo "下一步："
echo "  1. 查看测试模板: cat tests/TEST_TEMPLATE.md"
echo "  2. 查看使用文档: cat tests/README.md"
echo "  3. 运行所有测试: npm test"
echo "  4. 监听模式: npm run test:watch"
echo "  5. 生成覆盖率: npm run test:coverage"
echo ""
