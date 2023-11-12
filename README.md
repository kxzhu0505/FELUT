# FELUT
Source code of Exploration_of_FPGA_PLB_Architecture_Base_on_LUT_and_Microgates
To evaluate the proposed PLB structure (FE-LUT6), this project employs a Python script to invoke the aforementioned open-source EDA tools, realizing various stages of the evaluation process. 
The process comprises the following key steps: 
1) Utilizing Odin II for logic synthesis;
2) Employing ABC for technology mapping tailored to complex PLBs. This technology mapping involves the offline establishment of a Boolean matching function library and the invocation of a pre-built library for technology mapping (refer to Chapter Two for details); 
3) Utilizing VPR for packing, placement, routing, and timing analysis.



Usage：
1) Configure the paths in the global variables at the beginning of the script. Following the comments, organize the files that the script needs to read into specified folders. Place the `config.xml` file in `inputPath`, and create folders named `arch`, `blif`, and `verilog` within `inputPath`. Place the `arch` files in the `arch` folder, the `blif` files in the `blif` folder, and the `verilog` files in the `verilog` folder;
2) At the beginning of the script file, there are options for functional selection. Each option corresponds to a boolean parameter. If the parameter is set to true, the corresponding step is executed; if it is false, the step is not executed;
3) When running the Python script, a parameter "-Type <typename>" is required, where each distinct PLB structure corresponds to a different typename. The script will select the architecture file and the structural description string for DSD library generation based on the typename, and automatically generate the corresponding output file names.
