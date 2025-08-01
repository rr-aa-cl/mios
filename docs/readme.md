First, I compiled a docker image of mios with the libfranka version you need. You can find here: https://hub.docker.com/r/mirmi/mios Pull the image with the tag "0.15.0". That image is compiled with libfranka version 0.15.0.  Unfortunately, I don't have a FR3 at hand to test the image. Most probable, the automatic unlocking and FCI activation wont work. So you have to activate the FCI from the DESK interface. 

A easy way is to start mios from docker-compose. You can start a mongoDB (needed for mios) the same way. An example configuration is in the attachments.

As mios is implementing a realtime control of you robot based on libfranka, your PC needs to run on a realtime-kernel. I recommend simply installing the linux-xanmod-rt-x64v3 from here.

First startup: The first time you start mios, it will create a "miosL" database inside the mongoDB. It contains 2 collections: environment with all the teached poses. And parameters with default mios-parameters. Please insert the DESK username and password as well as the ControlBox IP into the database (miosL->parameters->system). You can use a GUI to do that. But you can also find a function inside the mios_examples.py (populate_database()).

I created a mios_examples.py (attachments) with some basic functionalities. You can find movement functions, insertion and extraction skills, position teaching and grasping commands in there. 

Here is also the published code on github. This is a mirror repository of our TUM-intern one without the development branches. Unfortunatelly, the automatic pushing stopped working. Therefore the repo is not quite up-to-date. If you want to compile it for yourself, you have to change the libfranka version inside the mios/cmake/FetchContent.cmake file. 



Here are some more prayers to the machine god:

Unpacking
Do not throw the foams and boxes away!! You might need them later for storing or shipping the robot.
Mounting
There is a small setup guide included in the box. You can have a look there on which cable goes where. There are also no screws included. For a proper mounting of the robot you need 4 M8 screws + lining discs and screw nuts.
Network-setup
This is only one possible way, build on years of experience. You should use a dedicated robot PC to run mios. This PC is connected to the ControlBox of the robot. Mios is then reachable from the network on port 12000.

To setup the network on the robot, you can use the desk interface of the panda just by connecting you PC to the Robot arm via ethernet. Than use your favorite browser to go to robot.franka.de or to 192.168.0.1 if you did't change the default IP. Accept the possible risk of a expired certificate and you are ready to use Desk. Here you can set set further network settings (burger menu->settings->network). Use a static IP for your Robot Control Box. I typically use 192.168.3.100 (subnetmask 255.255.255.0, gateway and DNS should be the static IP of your PC) 

But I think most you want to use the robot via the FCI interface meaning directly control the Robot torques / use MIOS. You can activate it from the desk interface. If you use the FCI you have to connect you PC to the Control Box and not to the robot arm. Set a fixed IP address for the ControlBox using Desk (e.g. 192.168.3.100). Also you need a fixed IP for your PC (192.168.3.1)
Feel free to ask questions
I am sure I haven't covered everything here. So, if you have any questions, please let me know.