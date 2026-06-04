# Stage 2 / visualization_agent — 图表包(Figure Package)

> 论文《认证之为结构》的三张图。代码见 `code/`,图件见 `code/figures/`。
> 全部图表为论文解析模型的数值图示 / 框架定性定位,非真实协议实测。

---

## 图 1(Figure 1)

**图 1** uncertified 相对 certified 的净延迟优势随恢复触发频率 ρ 的变化

*Note.* Δ_save = 2(uncertified 每轮节省的消息延迟);三条曲线对应不同的单次恢复成本 Δ_recover。圆点标出净优势归零的临界频率 ρ* = Δ_save/Δ_recover。本图为论文第 7.2 节解析成本模型的数值图示,非真实协议实测。

- **图件**:`code/figures/figure_1_net_advantage.pdf`
- **章节**:第 7 章(SubRQ3)
- **图表类型**:多线图(multi-line chart),对应 visualization_agent 决策树"趋势 / 多序列 ≤5"

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.78\columnwidth]{figures/figure_1_net_advantage.pdf}
    \caption{uncertified 相对 certified 的净延迟优势随恢复触发频率 $\rho$ 的变化}
    \label{fig:net-advantage}
    \floatfoot{\textit{注.} $\Delta_{save}=2$;曲线对应不同 $\Delta_{recover}$;圆点为临界频率 $\rho^*$。本图为解析模型的数值图示。}
\end{figure}
```

---

## 图 2(Figure 2)

**图 2** (ρ, Δ_recover) 参数空间中的 uncertified 优势区域

*Note.* 颜色表示净延迟优势(>0 即 uncertified 占优);黑色实线为临界边界 ρ* = Δ_save/Δ_recover(净优势为零的等高线),其左上方为优势区,右下方优势被抵消或反转。Δ_save = 2。本图为论文第 7 章解析成本模型的数值图示。

- **图件**:`code/figures/figure_2_advantage_region.pdf`
- **章节**:第 7.6 节(条件化结论)
- **图表类型**:热力图(heatmap)

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=0.85\columnwidth]{figures/figure_2_advantage_region.pdf}
    \caption{$(\rho,\Delta_{recover})$ 参数空间中的 uncertified 优势区域}
    \label{fig:advantage-region}
    \floatfoot{\textit{注.} 黑线为临界边界 $\rho^*$;其左上方 uncertified 占优。解析模型图示。}
\end{figure}
```

---

## 图 3(Figure 3)

**图 3** 深层设计轴上的协议定位

*Note.* 横轴为 availability-enforcement 时机(引用前 / 提交前 / 提交后),纵轴为单次 reconciliation 开销(定性)。本图按论文第 8 章提出的深层轴框架对语料库协议进行定性定位,坐标不代表实测数据。certified/uncertified 二分仅对应横轴两端,无法刻画 Adelie、DispersedLedger 等中间设计。

- **图件**:`code/figures/figure_3_design_axis.pdf`
- **章节**:第 8.3 节(用深层轴重新定位现有协议)
- **图表类型**:散点定位图(scatter / positioning map)

```latex
\begin{figure}[htbp]
    \centering
    \includegraphics[width=\columnwidth]{figures/figure_3_design_axis.pdf}
    \caption{深层设计轴上的协议定位}
    \label{fig:design-axis}
    \floatfoot{\textit{注.} 按第 8 章深层轴框架的定性定位,坐标非实测。}
\end{figure}
```

---

## 质量门核验(visualization_agent 10 项强制检查)

| # | 检查 | 结果 |
|---|------|------|
| 1 | 坐标轴标签 | ✅ 三图 x/y 轴均有描述性标签 |
| 2 | 单位标注 | ✅ 延迟轴标"消息延迟数",ρ 为频率 |
| 3 | 图例 | ✅ 图 1 有图例;图 2 有边界图例;图 3 用区域底色+标注 |
| 4 | APA 7.0 caption | ✅ 见上 |
| 5 | 色盲友好配色 | ✅ 分类用 CB 调色板;图 2 用 coolwarm 发散映射(蓝/红,非红绿) |
| 6 | 字号 ≥ 8pt | ✅ rcParams 最小 8pt |
| 7 | DPI ≥ 300 | ✅ savefig.dpi=300 |
| 8 | 尺寸符合栏宽 | ✅ 单/1.5 栏宽 |
| 9 | 数据准确 | ✅ 图 1/2 直接由解析式计算;模型经 Monte Carlo 仿真交叉验证(见 dag_bft_model.py 自检输出) |
| 10 | 无图表垃圾 | ✅ 无 3D、无饼图、无多余网格 |

**VLM 目视核验**:已渲染 PNG 并目检 2 轮——首轮发现图 1 ρ* 标签重叠、图 3 certified 簇标签重叠;已修正(图 1 错开标签偏移,图 3 改用引线标注)。当前版本无重叠、可读。
