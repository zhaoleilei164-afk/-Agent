import re
import os
from dataclasses import dataclass
from typing import List, Dict

# ====================== 数据结构定义 ======================
@dataclass
class CodeIssue:
    """代码问题结构体"""
    issue_type: str  # 错误类型
    line_num: int    # 错误行号
    description: str # 错误描述
    fix_suggestion: str # 修复建议

@dataclass
class OptimizeResult:
    """优化结果结构体"""
    original_code: str
    optimized_code: str
    improvements: List[str]

# ====================== 1. 解析Agent ======================
class EmbeddedParserAgent:
    """嵌入式代码解析Agent：识别寄存器、驱动、时序问题"""
    
    # STM32常用危险寄存器/错误配置
    DANGEROUS_REGISTERS = {
        "GPIOx_BSRR": "必须使用32位操作，禁止位带操作",
        "RCC_CR": "时钟配置错误会导致芯片死机",
        "FLASH_ACR": "等待周期配置错误会导致程序跑飞"
    }

    def __init__(self, code: str):
        self.code = code
        self.lines = code.split("\n")
        self.issues: List[CodeIssue] = []

    def analyze_gpio_config(self) -> None:
        """分析GPIO初始化配置问题"""
        for idx, line in enumerate(self.lines):
            line_num = idx + 1
            # 检测无时钟使能的GPIO初始化
            if "GPIO_Init" in line and "RCC_APB2PeriphClockCmd" not in self.code:
                self.issues.append(CodeIssue(
                    issue_type="硬件驱动错误",
                    line_num=line_num,
                    description="GPIO初始化未使能对应时钟",
                    fix_suggestion="添加 RCC_APB2PeriphClockCmd() 时钟使能代码"
                ))

    def analyze_register_safety(self) -> None:
        """分析寄存器安全配置问题"""
        for idx, line in enumerate(self.lines):
            line_num = idx + 1
            for reg, tip in self.DANGEROUS_REGISTERS.items():
                if reg in line and ("volatile" not in line and "(__IO" not in line):
                    self.issues.append(CodeIssue(
                        issue_type="寄存器风险",
                        line_num=line_num,
                        description=f"{reg} 寄存器未使用volatile声明，可能导致读写异常",
                        fix_suggestion=f"声明变量时添加 volatile 关键字：volatile {reg}"
                    ))

    def run_full_analysis(self) -> List[CodeIssue]:
        """执行完整解析"""
        self.analyze_gpio_config()
        self.analyze_register_safety()
        return self.issues

# ====================== 2. 调试Agent ======================
class DebugAgent:
    """调试Agent：自动解析报错日志，定位问题"""
    
    # 嵌入式常见错误映射
    ERROR_PATTERNS = {
        r"HardFault_Handler": "硬件故障，大概率是指针越界/寄存器配置错误",
        r"RCC_ClkInitFailed": "时钟初始化失败，检查晶振配置",
        r"GPIO_InitFailed": "GPIO初始化失败，未使能时钟或引脚冲突",
        r"Timeout": "硬件超时，检查外设接线/时序"
    }

    def debug_log(self, error_log: str) -> List[str]:
        """解析错误日志，输出调试方案"""
        solutions = []
        for pattern, solution in self.ERROR_PATTERNS.items():
            if re.search(pattern, error_log):
                solutions.append(f"[定位] {solution}")
        if not solutions:
            solutions.append("[未知错误] 请检查电源、接线或核心寄存器配置")
        return solutions

# ====================== 3. 优化Agent ======================
class OptimizeAgent:
    """优化Agent：代码格式化、补注释、优化规范"""
    
    def optimize(self, original_code: str) -> OptimizeResult:
        lines = original_code.split("\n")
        optimized = []
        improvements = []

        for idx, line in enumerate(lines):
            stripped = line.strip()
            # 1. 自动给初始化函数加注释
            if "GPIO_Init" in stripped and not line.strip().startswith("//"):
                optimized.append(f"    // 初始化GPIO引脚配置\n{line}")
                improvements.append("为GPIO初始化添加了标准注释")
            # 2. 规范时钟使能代码
            elif "RCC_APB2PeriphClockCmd" in stripped:
                optimized.append(f"    // 使能外设时钟（必须先于初始化）\n{line}")
                improvements.append("规范了时钟使能的注释格式")
            else:
                optimized.append(line)

        # 3. 补充volatile关键字
        final_code = "\n".join(optimized)
        for reg in EmbeddedParserAgent.DANGEROUS_REGISTERS:
            if reg in final_code and "volatile" not in final_code:
                final_code = final_code.replace(reg, f"volatile {reg}")
                improvements.append(f"为{reg}添加volatile安全声明")

        return OptimizeResult(
            original_code=original_code,
            optimized_code=final_code,
            improvements=improvements
        )

# ====================== 主程序：多Agent协同 ======================
class EmbeddedDebugOptimizeSystem:
    def __init__(self, code: str):
        self.code = code
        self.parser = EmbeddedParserAgent(code)
        self.debugger = DebugAgent()
        self.optimizer = OptimizeAgent()

    def run(self, error_log: str = ""):
        print("=" * 60)
        print("          嵌入式代码自动调试与优化 Agent 运行中")
        print("=" * 60)

        # 步骤1：解析Agent分析问题
        print("\n【1/3】解析Agent -> 代码静态分析")
        issues = self.parser.run_full_analysis()
        if not issues:
            print("✅ 未发现代码问题")
        else:
            for issue in issues:
                print(f"❌ 行{issue.line_num} | {issue.issue_type} | {issue.description}")
                print(f"   修复建议：{issue.fix_suggestion}\n")

        # 步骤2：调试Agent分析报错
        print("【2/3】调试Agent -> 错误日志分析")
        if error_log:
            solutions = self.debugger.debug_log(error_log)
            for s in solutions:
                print(f"🔍 {s}")
        else:
            print("ℹ️  无错误日志，跳过调试")

        # 步骤3：优化Agent优化代码
        print("\n【3/3】优化Agent -> 代码规范优化")
        result = self.optimizer.optimize(self.code)
        print("\n✅ 优化完成，优化项：")
        for imp in result.improvements:
            print(f"   ✔ {imp}")

        # 输出优化后代码
        print("\n" + "-"*50)
        print("优化后的嵌入式代码：")
        print("-"*50)
        print(result.optimized_code)

# ====================== 测试用例（STM32 GPIO初始化代码） ======================
if __name__ == "__main__":
    # 待优化的嵌入式源码（有问题的版本）
    test_embedded_code = """
void GPIO_Configuration(void)
{
    GPIO_InitTypeDef GPIO_InitStructure;
    
    // 配置PA0为推挽输出
    GPIO_InitStructure.GPIO_Pin = GPIO_Pin_0;
    GPIO_InitStructure.GPIO_Mode = GPIO_Mode_Out_PP;
    GPIO_InitStructure.GPIO_Speed = GPIO_Speed_50MHz;
    GPIO_Init(GPIOA, &GPIO_InitStructure);
    
    // 操作寄存器
    GPIOA_BSRR = 0x0001;
}
"""

    # 模拟报错日志
    test_error_log = "HardFault_Handler Triggered"

    # 启动Agent系统
    system = EmbeddedDebugOptimizeSystem(test_embedded_code)
    system.run(error_log=test_error_log)
