# Install phyml & RAxML for use with Partitionfinder

Partitionfinder relies on two tools as dependencies: phyml and RAxML.
For linux & OSX both tools can be donwloaded, compiled and added to pathfinder
using the install.sh script in this directory. For windows please refer to 
the file BUILDING.txt in this directory.



# Requirement
The installation of phyml requires libtool and autoconf packages. The provided
install script will check for them and try to install them in case they are
missing using one of the following package managers: brew, yum or apt-get.


# Installation 

Open a terminal/console and locate the partitionfinder root directory and change 
to directory PARTITIONFINDER_ROOT/programs. Type

    $> ./install.sh

and follow the instructions.


