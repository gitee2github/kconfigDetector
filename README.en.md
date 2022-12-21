# kconfigDetector

#### Description
kconfigDetector is a series of detection tools provided for kernel configuration, which include:
* kconfigDepDetector  
  kernel configuration  error value detection tool.  
  Based on the Kconfig definition of each configuration item in the kernel source code, it detects the error values in the kernel configuration file that do not satisfy the constraints of dependencies and fetches, and provides a query function for parent and child configuration items.
  
#### Software Architecture
* Basic logic for error value detection
  + Preprocessing: Read all the Kconfig content to be parsed to generate the ".Kconfig" file
  + Parse: Grammar analysis, read the .Kconfig file and generate the data structure of the node tree
  + Checker: Based on the syntax analysis results, check whether the profile takes values that satisfy the constraint logical expressions

#### Installation

1.  Installing dependencies
   > yum install -y python3  
   > pip3 install ply
2.  Get Code
   > git clone https://gitee.com/openeuler/kconfigDetector.git


#### Instructions

* kconfigDepDetector  
1.  Run command  
   check_kconfig_dep.py <OPTIONS>  
   
   Parameter Description
   - OPTIONS

| Parameter | Description |
| ---- | ---- |
| --checkfile, -c | Required, profile to be checked  |
| --kernelversion, -v  | Required, kernel version  |
| --kernelpath, -s | Optional, kernel source path (required for the first check of this version)|
| --output, -o | Optional, the output path of the detect result, default current directory|
| --arch, -a | Optional, target architecture, local architecture of the default check environment |  
  
  
2.  Output  
   After running, the check result file version_architecture_error.json is output, and the error message is printed in the terminal category as follows  
   > ---------error type: num-------------  
   > [Configuration item name]  
   >    value = Configuration item value  
   >    path = Configuration item definition file path  
   >    type = Configuration item type (printed only on type error)  
   >    rev_select = Expression and value of the parent configuration item for forced selection (printed only when unmet dependence)  
   >    depends =  Expressions and values of parent configuration items for dependencies (printed only when depends error and unmet dependence)  
   >    restrict = Expression and value of the value constraint (printed only in case of range error and restrict warning)  
   

   Error types include：  
   - type error: The value of the configuration item does not match the type.
   - depends error: The configuration item is not started by select and the dependency is not satisfied.
   - lack config: The specified configuration item is not found in the kernel Kconfig file.
   - range error: Does not meet the range of values specified by range.
   - restrict warning: The value of the configuration item does not meet the requirements, usually for the default or simply keyword.
   - unmet dependence: The configuration item is forced to start by select, but the dependency is not satisfied.

#### Contribution

1.  Fork the repository
2.  Create Feat_xxx branch
3.  Commit your code
4.  Create Pull Request

