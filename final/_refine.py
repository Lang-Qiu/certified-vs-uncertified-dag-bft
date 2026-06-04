# -*- coding: utf-8 -*-
"""Source-level refinements on final_paper.md (user-requested, 2026-06-04 round 2).
Order matters: title -> abstracts -> author voice -> gloss removal -> quote curl.
None of these change any number, statistic, citation [n], figure ref, or claim."""
import re

F = 'final_paper.md'
t = open(F, encoding='utf-8').read()
orig = t

# --- (3) title -------------------------------------------------------------
NEW_TITLE = 'DAG-BFT 共识中认证机制的结构性作用：去认证设计的隐性代价与性能边界'
t = re.sub(r'\A# .*\n', '# ' + NEW_TITLE + '\n', t, count=1)

# --- (1)+(2) abstracts: shorter, fewer English glosses ---------------------
NEW_ZH = ('有向无环图(DAG)型拜占庭容错(BFT)共识近年从 certified 转向 uncertified,'
'以移除每区块认证换取更低延迟;这一优势多被视为结构性的——少一轮可靠广播(RBC)即少一轮延迟。'
'本文质疑此判断。现有 certified 与 uncertified 的比较混淆变量未受控:二者除认证外尚有十余处设计差异,'
'将延迟差直接归因于去认证并不可靠。为此本文提出一个以安全性与活性不变量为硬边界的受控分析框架,'
'隔离认证强度这一单一变量,并论证:移除认证不是可分离的性能优化,而是一次结构性替换——'
'认证承载的三个不变量(非等价性、数据可用性、因果历史完整性)并未消失,只是被重新分配到其他组件。'
'关键的不对称在于:逻辑型不变量可被低成本平移,物理型的数据可用性只能被弱化并补偿;'
'隐性代价因而集中于可用性,且仅在故障时爆发,是一笔或有负债而非固定开销。'
'本文进一步在异步模型下论证非等价性必须被 enforce,从而说明 uncertified 的延迟优势是条件性的。'
'真正决定协议行为的深层设计轴,是可用性的 enforcement 机制与协调修复触发条件,'
'而非 certified/uncertified 这一浅层标签。该结论的或有负债侧已由真实 Sui n=7/n=4 部署的'
'受控故障注入(290+ 次重复)初步支持:故障代价确为非线性、由故障强度驱动的或有负债(详见 §7.6.1)。')

NEW_EN = ('DAG-based Byzantine Fault Tolerant (BFT) consensus has recently shifted from '
'certified to uncertified DAGs, trading per-block certification for lower commit latency—an '
'advantage widely treated as structural: one fewer round of Reliable Broadcast (RBC) means one '
'fewer round of latency. This paper challenges that judgment. Existing certified-versus-'
'uncertified comparisons are confounded: the two families differ along more than a dozen design '
'dimensions, so attributing the latency gap to de-certification alone is unsafe. We therefore '
'propose a controlled analytical framework that draws module boundaries along safety and '
'liveness invariants, isolating certification strength as a single variable, and argue that '
'removing certification is not a separable optimization but a structural substitution: the '
'three invariants it carries—non-equivocation, data availability, and causal-history '
'integrity—are reassigned rather than eliminated. The key asymmetry is that logical invariants '
'relocate cheaply, whereas physical data availability can only be weakened and compensated, so '
'the hidden cost concentrates on availability as a contingent liability that materializes only '
'under faults. We further argue, in the asynchronous model, that non-equivocation must be '
'enforced, making the latency advantage conditional. The genuine design axis is the '
'availability-enforcement mechanism and its reconciliation trigger, not the surface '
'certified/uncertified label. This contingent-liability side is preliminarily supported by '
'controlled fault-injection on a real Sui n=7/n=4 deployment (290+ repetitions): the '
'fault-induced latency cost is a non-linear, fault-intensity-driven contingent liability.')

t = re.sub(r'(## 摘要\n\n).*?(\n\n\*\*关键词)', lambda m: m.group(1) + NEW_ZH + m.group(2), t, count=1, flags=re.S)
t = re.sub(r'(## Abstract\n\n).*?(\n\n\*\*Keywords)', lambda m: m.group(1) + NEW_EN + m.group(2), t, count=1, flags=re.S)

# --- (5) single-author voice ----------------------------------------------
n_team = t.count('本团队'); t = t.replace('本团队', '本人')
n_we = t.count('我们'); t = t.replace('我们', '本文')

# --- (4) remove redundant English glosses (keep names/acronyms/metrics/stats) ---
collapse = {
 '(Directed Acyclic Graph, DAG)': '(DAG)',
 '(Byzantine Fault Tolerant, BFT)': '(BFT)',
 '(Reliable Broadcast, RBC)': '(RBC)',
 '(State Machine Replication, SMR)': '(SMR)',
 '(Maximal Extractable Value, MEV)': '(MEV)',
}
for a, b in collapse.items():
    t = t.replace(a, b)

drop = ['(confounding)', '(invariant)', '(structural substitution)', '(contingent liability)',
 '(de-certification)', '(internal validity)', '(amortized cost)', '(Proof-of-Work)',
 '(common prefix)', '(chain quality)', '(total-order broadcast)', '(metastable)',
 '(partial synchrony)', '(responsiveness)', '(sharding)', '(clan)', '(reframe)',
 '(relocated)', '(weakened-and-compensated)', '(eliminated)', '(consistency)',
 '(correctness)', '(integrity)', '(totality)', '(certificate)', '(best-effort)',
 '(worked example)', '(argument)', '(proof sketch)', '(accountability)', '(message delay)',
 '(view-change)', '(implementation cross-check)', '(workload skew)', '(substructure)',
 '(superstructure)', '(relabeling)', '(order-fairness)', '(late-binding)',
 '(data-availability sampling)', '(rotation)', '(round)', '(skip)']
n_drop = 0
for g in drop:
    n_drop += t.count(g); t = t.replace(g, '')

# --- (0) straight double quotes -> directional Chinese quotes “ ” ----------
n_q = t.count('"')
t = re.sub(r'"([^"]*)"', lambda m: '“' + m.group(1) + '”', t)
left = t.count('"')

open(F, 'w', encoding='utf-8').write(t)
print(f'title set | abstracts replaced | 本团队->本人 x{n_team} | 我们->本文 x{n_we} '
      f'| glosses dropped x{n_drop} (+5 collapsed) | quotes curled {n_q}->{left} straight left')
print('zh-abstract chars:', len(NEW_ZH), ' en-abstract words:', len(NEW_EN.split()))
