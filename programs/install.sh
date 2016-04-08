#!/bin/bash



### Basic installation file for phyml and raxml
# 
#

INSTALL_DIR=`pwd`



# Remove windows/Mac executables of phyml and raxml
# from partitionfinder directory
rm $INSTALL_DIR/phyml{,.exe} $INSTALL_DIR/raxml{,.exe}

# check if phyml is already installed
# and get version number
PHYML_INSTALL=1
PHYML_VERSION=$(phyml --version 2>&1)

if [[ "${PHYML_VERSION}" == *"PhyML version"* ]]; then
    if [[ "${PHYML_VERSION}" != *"PhyML version 20160326"* ]]; then
        while true; do
            read -p "Found un-tested phyml version. Do you want to install version 20160325 in the partitionfinder directory [Yn]?" yn
            case $yn in
                Y ) break;;
                n ) PHYML_INSTALL=0; break;;
                * ) "Please answer either Y for yes or n for no." 
            esac
        done
    fi
fi


# check for brew/yum/apt-get
REPO=""
if [[ $(command -v apt-get) ]]; then
	REPO="apt"
elif [[ $(command -v brew) ]]; then
	REPO="brew"
elif [[ $(command -v yum) ]]; then
	REPO="yum"
else
	echo "No package manager found."
	exit
fi


# download and install phyml if needed
if [[ "${PHYML_INSTALL}" == 1 ]]; then

	# check for package manager
	# and install autoreconf 
	if [[ ! $(command -v autoreconf) ]]; then
		echo "Missing package autoconf. Attempting to install using package manager." 
		case $REPO in
			apt ) sudo apt-get install autoconf;;
			brew ) brew install autoconf;;
			yum ) yum install autoconf;;
			* ) "No package manager found. Please install autoconf manually and retry."; exit;;
		esac
	fi

	# install lintool if needed 
	if [[ ! $(command -v libtool) ]]; then
		echo "Missing package libtool. Attempting to install using package manager." 
		case $REPO in
			apt ) sudo apt-get install libtool;;
			brew ) brew install libtool;;
			yum ) yum install libtool;;
			* ) "No package manager found. Please install libtool manually and retry."; exit;;
		esac
	fi

    TMP_DIR=$INSTALL_DIR/tmp
    mkdir $TMP_DIR
    cd $TMP_DIR
    wget https://github.com/stephaneguindon/phyml/archive/7be3a4cb04eae72d9309a34a4727938371909200.zip
    unzip ./7be3a4cb04eae72d9309a34a4727938371909200.zip
    cd ./phyml-7be3a4cb04eae72d9309a34a4727938371909200 

	
	./autogen.sh && ./configure && make

	if [[ $? != "0" ]]; then
		exit
	fi

    mv ./src/phyml ../..
    cd ../..
    rm -rf ./tmp
fi

# check if raxml (threaded & unthreaded) is installed
# If so, set symlink to installed version
if [[ $(command -v raxmlHPC-AVX2) ]]; then
    RAXML_HPC=$(command -v raxmlHPC-AVX2)
#    ln -s ${RAXML_HPC} ${INSTALL_DIR}/raxml
    break;
elif [[ $(command -v raxmlHPC-SSE3) ]]; then
    RAXML_HPC=$(command -v raxmlHPC-SSE3)
    ln -s ${RAXML_HPC} ${INSTALL_DIR}/raxml
fi

if [[ $(command -v raxmlHPC-PTHREADS-AVX2) ]]; then
    RAXML_THREADED=$(command -v raxmlHPC-PTHREADS-AVX2)
#    ln -s ${RAXML_THREADED} ${INSTALL_DIR}/raxml_thread
    break;
elif [[ $(command -v raxmlHPC-PTHREADS-SSE3) ]]; then
    RAXML_THREADED=$(command -v raxmlHPC-PTHREADS-SSE3)
    ln -s ${RAXML_THREADED} ${INSTALL_DIR}/raxml_threaded
fi

if [[ ! $(command -v ${INSTALL_DIR}/raxml) ]]; then
    TMP_DIR=$INSTALL_DIR/tmp
    mkdir $TMP_DIR
    cd $TMP_DIR
    wget https://github.com/stamatak/standard-RAxML/archive/68c878e90f55c29e67b6bdd9ad336f9439c70cdd.zip
    unzip ./68c878e90f55c29e67b6bdd9ad336f9439c70cdd.zip
    cd standard-RAxML-68c878e90f55c29e67b6bdd9ad336f9439c70cdd
   
    # What instruction set is supported (SSE3/AVX2/AVX) 
    RAXML_MAKE=''
    RAXML_THREADED_MAKE=''
    RAXML_EXEC=''
    RAXML_THREADED_EXEC=''
    if [[ $(grep 'avx2' /proc/cpuinfo) ]]; then
        RAXML_MAKE='Makefile.AVX2.gcc'
        RAXML_THREADED_MAKE='Makefile.AVX2.PTHREADS.gcc'
        RAXML_EXEC='raxmlHPC-AVX2'
        RAXML_THREADED_EXEC='raxmlHPC-PTHREADS-AVX2'
    elif [[ $(grep 'sse3\|pni' /proc/cpuinfo) ]]; then
        RAXML_MAKE='Makefile.SSE3.gcc'
        RAXML_THREADED_MAKE='Makefile.SSE3.PTHREADS.gcc'
        RAXML_EXEC='raxmlHPC-SSE3'
        RAXML_THREADED_EXEC='raxmlHPC-PTHREADS-SSE3'
    elif [[ $(grep 'avx' /proc/cpuinfo) ]]; then
        RAXML_MAKE='Makefile.AVX.gcc'
        RAXML_THREADED_MAKE='Makefile.AVX.PTHREADS.gcc'
        RAXML_EXEC='raxmlHPC-AVX'
        RAXML_THREADED_EXEC='raxmlHPC-PTHREADS-AVX'
    else
        echo "\nNo AVX/AVX/SSE3 support.\n"
        RAXML_TYPE='Makefile.gcc'
        RAXML_THREADED_MAKE='Makefile.PTHREADS.gcc'
        RAXML_EXEC='raxmlHPC'
        RAXML_THREADED_EXEC='raxmlHPC-PTHREADS'
    fi

    # compile appropriate raxml version
    make -f ${RAXML_MAKE}
    rm *.o
    
    make -f ${RAXML_THREADED_MAKE}
    rm *.o

    mv ./${RAXML_EXEC} ${INSTALL_DIR}/raxml
    mv ./${RAXML_THREADED_EXEC} ${INSTALL_DIR}/raxml_threaded
    cd ../../
    rm -rf ${INSTALL_DIR}/tmp
fi





 

