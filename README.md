# kconfigDetector

#### 介绍
kconfigDetector是为内核配置提供的一系列检测工具. 包括：  
* kconfigDepDetector 内核配置项错误值检测工具   
  依据内核源码中各配置项的Kconfig定义，检测出内核配置文件中不满足依赖、取值等约束条件的错误值，并提供父类和子类配置项查询功能。  


#### 软件架构
* 错误值检测基本逻辑  
    + 预处理（Preprocessing），读取所有需要解析的Kconfig内容生成".Kconfig"文件
    + 语法分析（Parse），读取.Kconfig文件，生成节点树的数据结构
    + 检查配置文件（Checker），根据语法分析结果，检查配置文件取值是否满足约束条件的逻辑表达式


#### 安装教程

1.  安装依赖
   > yum install -y python3  
   > pip3 install ply
2.  获取代码
   > git clone https://gitee.com/openeuler/kconfigDetector.git

#### 使用说明
* kconfigDepDetector  
1.  运行命令  
   check_kconfig_dep.py <OPTIONS>  
   
   参数说明
   - OPTIONS

| 参数 | 描述 |
| ---- | ---- |
| --checkfile, -c | 必填，待检查配置文件  |
| --kernelversion, -v  | 必填，内核版本  |
| --kernelpath, -s | 可选，内核源码路径（该版本首次检查必填）|
| --output, -o | 可选，检查结果输出路径，默认当前目录 |
| --arch, -a       | 可选，目标体系架构，默认检查环境的本地架构 |  
  
  
2.  输出说明  
   运行完成后，输出检查结果文件 版本号_架构_error.json，并在终端分类打印错误信息如下  
   > ---------错误类型: 个数-------------  
   > [配置项名称]  
   >    value = 取值  
   >    path = 配置项定义文件路径  
   >    type = 配置项类型   （仅在type error时打印）  
   >    rev_select = 强制选择的父类配置项表达式及取值   （仅在unmet dependence时打印）  
   >    depends =  依赖关系的父类配置项表达式及取值   （仅在depends error和unmet dependence时打印）  
   >    restrict = 取值约束的表达式及取值    （仅在range error和restrict warning时打印）  
   

   错误类型包括：  
   - 类型错误: type error, 配置项取值与类型不符
   - 依赖不满足: depends error, 配置项未通过select启动且依赖不满足
   - 未找到配置项: lack config, 未在内核Kconfig文件中找到指定配置项
   - range未满足: range error，不满足range规定的取值范围
   - 取值告警: restrict warning, 配置项取值未满足要求, 通常为default或imply关键字
   - 依赖风险: unmet dependence, 配置项通过select强制启动, 但是依赖未满足


#### 参与贡献

1.  Fork 本仓库
2.  新建 Feat_xxx 分支
3.  提交代码
4.  新建 Pull Request

