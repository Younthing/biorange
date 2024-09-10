### SMINA 使用说明书

SMINA 是 Autodock Vina（http://vina.scripps.edu/）的一个分支，专注于改进评分和最小化。与标准 Vina（版本 1.1.2）相比，SMINA 的变化包括：

- 全面支持配体分子格式（通过 OpenBabel）\*
- 支持多配体文件（例如，sdf 文件）\*
- 支持附加项类型（例如，去溶剂化，静电）
- 支持自定义用户参数化的评分函数（参见 --custom_scoring）
- 基于用户指定的绑定配体自动创建盒子
- 允许输出超过 20 个对接构象
- 大大改进的最小化算法（--minimize 直到收敛）

对于使用 AutoDock Vina 进行最小化（local_only）而不是对接的工作流程，这些更改使 Vina 更易于使用且速度提高 10-20 倍。由于部分电荷计算和文件 I/O 不是性能的主要部分，对接性能大致相同。

如果你发现 SMINA 有用，请引用我们的论文：http://pubs.acs.org/doi/abs/10.1021/ci300604z

\*非 pdbqt 配体文件必须添加部分电荷。这是通过 OpenBabel 完成的，结果会与 AutoDock Tools 附带的 prepare_ligand4.py 脚本不同。

预构建的二进制文件是在 Ubuntu 14.04 上构建的。主要依赖项是 boost（1.54）和 openbabel。如果这些依赖项无法满足，提供了一个静态二进制文件（但是，如果内核版本低于 2.6.24，可能仍然无法工作）。

### 输入参数

- `-r [ --receptor ] arg`：受体的刚性部分（PDBQT）
- `--flex arg`：如果有的话，柔性侧链（PDBQT）
- `-l [ --ligand ] arg`：配体
- `--flexres arg`：通过逗号分隔的链：残基列表指定的柔性侧链
- `--flexdist_ligand arg`：用于 flexdist 的配体
- `--flexdist arg`：将所有侧链设置为指定距离内的 flexdist_ligand 为柔性

### 搜索空间（必需）

- `--center_x arg`：中心的 X 坐标
- `--center_y arg`：中心的 Y 坐标
- `--center_z arg`：中心的 Z 坐标
- `--size_x arg`：X 维度的大小（埃）
- `--size_y arg`：Y 维度的大小（埃）
- `--size_z arg`：Z 维度的大小（埃）
- `--autobox_ligand arg`：用于自动盒子的配体
- `--autobox_add arg`：添加到自动生成盒子的缓冲空间量（默认在所有六个面上 +4）
- `--no_lig`：无配体；用于采样/最小化柔性残基

### 评分和最小化选项

- `--custom_scoring arg`：自定义评分函数文件
- `--score_only`：仅对提供的配体构象进行评分
- `--local_only`：仅使用 autobox 进行局部搜索（你可能想使用 --minimize）
- `--minimize`：能量最小化
- `--randomize_only`：生成随机构象，尝试避免冲突
- `--minimize_iters arg (=0)`：最速下降法的迭代次数；默认值随转子数量变化，通常不足以收敛
- `--accurate_line`：使用精确的线搜索
- `--minimize_early_term`：在完全满足收敛条件之前停止最小化
- `--approximation arg`：使用的近似（线性，样条或精确）
- `--factor arg`：近似因子：值越高，近似越精细
- `--force_cap arg`：允许的最大力；较低的值更温和地最小化冲突结构
- `--user_grid arg`：用于用户网格数据计算的 Autodock 映射文件
- `--user_grid_lambda arg (=-1)`：缩放 user_grid 和功能评分
- `--print_terms`：打印所有可用的术语及默认参数化
- `--print_atom_types`：打印所有可用的原子类型

### 输出（可选）

- `-o [ --out ] arg`：输出文件名，格式取自文件扩展名
- `--out_flex arg`：柔性受体残基的输出文件
- `--log arg`：可选，写入日志文件
- `--atom_terms arg`：可选，写入每个原子的相互作用项值
- `--atom_term_data`：嵌入输出 sd 数据中的每个原子的相互作用项

### 杂项（可选）

- `--cpu arg`：要使用的 CPU 数量（默认是尝试检测 CPU 数量，失败时使用 1）
- `--seed arg`：显式随机种子
- `--exhaustiveness arg (=8)`：全局搜索的详尽性（大致与时间成正比）
- `--num_modes arg (=9)`：生成的最大结合模式数量
- `--energy_range arg (=3)`：最佳结合模式和显示的最差模式之间的最大能量差（kcal/mol）
- `--min_rmsd_filter arg (=1)`：用于过滤最终构象以消除冗余的 rmsd 值
- `-q [ --quiet ]`：抑制输出消息
- `--addH arg`：自动在配体中添加氢（默认开启）
- `--flex_hydrogens`：启用仅影响氢的扭转（例如 OH 基团）。这很愚蠢，但提供了与 Vina 的兼容性。

### 配置文件（可选）

- `--config arg`：可以在此处放置上述选项

### 信息（可选）

- `--help`：显示使用摘要
- `--help_hidden`：显示带有隐藏选项的使用摘要
- `--version`：显示程序版本

### 自定义评分文件

自定义评分文件由权重、术语描述和每行的可选注释组成。术语描述的数值参数可以变化以参数化评分函数。使用 --print_terms 查看所有可用术语。

示例（所有权重为 1.0，列出了所有术语类型）：

```
1.0  ad4_solvation(d-sigma=3.6,_s/q=0.01097,_c=8)  去溶剂化，q 决定值是否与电荷相关
1.0  ad4_solvation(d-sigma=3.6,_s/q=0.01097,_c=8)  在所有术语中，c 是距离截止
1.0  electrostatic(i=1,_^=100,_c=8)  i 是距离的指数，详情见 everything.h
1.0  electrostatic(i=2,_^=100,_c=8)
1.0  gauss(o=0,_w=0.5,_c=8)  o 是偏移量，w 是高斯的宽度
1.0  gauss(o=3,_w=2,_c=8)
1.0  repulsion(o=0,_c=8)  o 是平方距离排斥的偏移量
1.0  hydrophobic(g=0.5,_b=1.5,_c=8)  g 是良好距离，b 是不良距离
1.0  non_hydrophobic(g=0.5,_b=1.5,_c=8)  值在 g 和 b 之间线性插值
1.0  vdw(i=4,_j=8,_s=0,_^=100,_c=8)  i 和 j 是 LJ 指数
1.0  vdw(i=6,_j=12,_s=1,_^=100,_c=8)  s 是平滑度，^ 是上限
1.0  non_dir_h_bond(g=-0.7,_b=0,_c=8)  良好和不良
1.0  non_dir_h_bond_quadratic(o=0.4,_c=8)  类似于排斥，但用于氢键，不要使用
1.0  non_dir_h_bond_lj(o=-0.7,_^=100,_c=8)  LJ 10-12 势，限制在 ^
1.0  acceptor_acceptor_quadratic(o=0,_c=8)  氢键受体之间的二次势
1.0  donor_donor_quadratic(o=0,_c=8)  氢键供体之间的二次势
1.0  num_tors_div  div 常数项不是线性独立的
1.0  num_heavy_atoms_div
1.0  num_heavy_atoms  这些项只是相加
1.0  num_tors_add
1.0  num_tors_sqr
1.0  num_tors_sqrt
1.0  num_hydrophobic_atoms
1.0  ligand_length
```

### 原子类型术语

你可以在特定原子类型对之间定义自定义函数：

```
atom_type_gaussian(t1=,t2=,o=0,_w=0,_c=8)  指定原子类型之间的高斯势
atom_type_linear(t1=,t2=,g=0,_b=0,_c=8)  指定原子类型之间的线性势
atom_type_quadratic(t1=,t2=,o=0,_c=8)  指定原子类型之间的二次势
atom_type_inverse_power(t1=,t2=,i=0,_^=100,_c=8)  指定原子类型之间的反幂势
```

使用 --print_atom_types 查看所有可用的原子类型。请注意，尽管有原子类型，氢总是被忽略。

请注意，这些都是对称的 - 你不需要为 (t1,t2) 和 (t2,t1) 指定术语（这样做只会使势的值加倍）。

### 示例：伪造共价对接

考虑以下自定义评分函数：

```
-0.035579    gauss(o=0,_w=0.5,_c=8)
-0.005156    gauss(o=3,_w=2,_c=8)
0.840245     repulsion(o=0,_c=8)
-0.035069    hydrophobic(g=0.5,_b=1.5,_c=8)
-0.587439    non_dir_h_bond(g=-0.7,_b=0,_c=8)
1.923        num_tors_div
-100.0       atom_type_gaussian(t1=Chlorine,t2=Sulfur,o=0,_w=3,_c=8)
```

除了最后一项外，所有项都是默认的 Vina 评分函数。最后一项在 Cl 和 S 之间应用了非常强的高斯势。在我们对接的系统中，我们将两个已知形成共价键的原子修改为氯和硫（系统不物理，但没关系）。由于这些是系统中唯一的 Cl 和 S，并且该项具有较大的权重，最佳对接解决方案都将这些原子放在一起。然后可以仅使用默认评分函数重新评分/最小化最终构象。
