#!/usr/bin/env python

# Software License Agreement (BSD License)
#
# Copyright (c) 2013, Willow Garage, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of Willow Garage, Inc. nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#
# Author: Ioan Sucan

import sys
import rospy
from moveit_commander import RobotCommander, PlanningSceneInterface, MoveGroupCommandInterpreter, roscpp_initialize, roscpp_shutdown
from geometry_msgs.msg import PoseStamped
from geometry_msgs.msg import Pose
from sensor_msgs.msg import Joy
from robotiq_s_model_articulated_msgs.msg import SModelRobotOutput
from trajectory_msgs.msg import *
from control_msgs.msg import *
import actionlib
import tf

interpreter = None
left_arm = False
right_arm = False
gripper_mode = False
ptu_mode = False

gripper_publisher = None
gripper_cmd = None

left_gripper_closed = False
right_gripper_closed = False

left_gripper_rotation = 0
right_gripper_rotation = 0

left_arm_client = None
right_arm_client = None

LEFT_JOINT_NAMES = ['l_ur5_arm_shoulder_pan_joint', 'l_ur5_arm_shoulder_lift_joint', 'l_ur5_arm_elbow_joint', 'l_ur5_arm_wrist_1_joint', 'l_ur5_arm_wrist_2_joint', 'l_ur5_arm_wrist_3_joint']
RIGHT_JOINT_NAMES = ['r_ur5_arm_shoulder_pan_joint', 'r_ur5_arm_shoulder_lift_joint', 'r_ur5_arm_elbow_joint', 'r_ur5_arm_wrist_1_joint', 'r_ur5_arm_wrist_2_joint', 'r_ur5_arm_wrist_3_joint']
Q1 = [1.57, -1.57, 0, -1.57, 0, 0]
Q2 = [-1.57, -1.57, 0, -1.57, 0, 0]
Q3 = [-1.57, -0.1745, -2.79, -1.57, 0, 0]

# Definitions for predefined locations
GRAB_OUT = 0
GRAB_IN = 1
GRAB_ABOVE = 2
GRAB_BELOW = 3
GRAB_FRONT = 4
CARRY = 5
DROP_OFF = 6
FRONTAL_GRAB = 7

LEFT_ARM = 0
RIGHT_ARM = 1

left_arm_joint_settings = [[]]
left_arm_pose_settings = [[]]
left_arm_rpy_settings = [[]]

right_arm_joint_settings = [[]]
right_arm_pose_settings = [[]]
right_arm_rpy_settings = [[]]


def go_to_predefined(conf)
    global GRAB_OUT
    global GRAB_IN
    global GRAB_ABOVE
    global GRAB_BELOW
    global GRAB_FRONT
    global CARRY
    global DROP_OFF
    global FRONTAL_GRAB
    global interpreter
    global LEFT_ARM
    global RIGHT_ARM
    global left_arm_joint_settings
    global left_arm_pose_settings
    global left_arm_rpy_settings
    global right_arm_joint_settings
    global right_arm_pose_settings
    global right_arm_rpy_settings
  
    joint_settings = None
    pose_settings = None
    rpy_settings = None

    arm = None

    group = interpreter.get_active_group()
    joints = group.get_joints()
    joint1 = joints[0]
    
    if joint1[0] is "l":
        arm = 0
    elif joint1[0] is "r":
        arm = 1

    if arm is 0:
        joint_settings = left_arm_joint_settings
        rpy_settings = left_arm_rpy_settings
        pose_settings = left_arm_pose_settings
    elif arm is 1:
        joint_settings = right_arm_joint_settings
        rpy_settings = right_arm_rpy_settings
        pose_settings = right_arm_pose_settings 

    if arm is not None:
        group.set_joint_value_target(joint_settings[conf])
        group.set_rpy_target(rpy_settings[conf])
        group.set_pose_target(pose_settings[conf])

        group.go()

def move_home():
    global interpreter
    group = interpreter.get_active_group()
    global left_arm_client
    global right_arm_client
    j = group.get_joints()
    JOINTS = None
    client = None
    if j[0][0] is "l": 
        client = left_arm_client
        JOINTS = LEFT_JOINT_NAMES
    elif j[0][0] is "r":
        client = right_arm_client
        JOINTS = RIGHT_JOINT_NAMES

    g = FollowJointTrajectoryGoal()
    g.trajectory = JointTrajectory()
    g.trajectory.joint_names = JOINTS 
    g.trajectory.points = [
        JointTrajectoryPoint(positions=group.get_current_joint_values(), velocities=[0]*6, time_from_start=rospy.Duration(0.0)),
        JointTrajectoryPoint(positions=Q1, velocities=[0]*6, time_from_start=rospy.Duration(2.0)), 
        JointTrajectoryPoint(positions=Q2, velocities=[0]*6, time_from_start=rospy.Duration(3.0)),
        JointTrajectoryPoint(positions=Q3, velocities=[0]*6, time_from_start=rospy.Duration(6.0))]
    client.send_goal(g)
    rospy.loginfo("Moved arm to home position")
    try:
        client.wait_for_result()
    except KeyboardInterrupt:
        client.cancel_goal()
        raise


def genCommand(char, command):
    """Update the command according to the character entered by the user."""    
        
    if char == 'a':
        command = SModelRobotOutput();
        command.rACT = 1
        command.rGTO = 1
        command.rSPA = 255
        command.rFRA = 150

    if char == 'r':
        command = SModelRobotOutput();
        command.rACT = 0

    if char == 'c':
        command.rPRA = 255

    if char == 'o':
        command.rPRA = 0

    if char == 'b':
        command.rMOD = 0
        
    if char == 'p':
        command.rMOD = 1
        
    if char == 'w':
        command.rMOD = 2
        
    if char == 's':
        command.rMOD = 3

    #If the command entered is a int, assign this value to rPRA
    try: 
        command.rPRA = int(char)
        if command.rPRA > 255:
            command.rPRA = 255
        if command.rPRA < 0:
            command.rPRA = 0
    except ValueError:
        pass                    
        
    if char == 'f':
        command.rSPA += 25
        if command.rSPA > 255:
            command.rSPA = 255
            
    if char == 'l':
        command.rSPA -= 25
        if command.rSPA < 0:
            command.rSPA = 0

            
    if char == 'i':
        command.rFRA += 25
        if command.rFRA > 255:
            command.rFRA = 255
            
    if char == 'd':
        command.rFRA -= 25
        if command.rFRA < 0:
            command.rFRA = 0

    return command

def rotate_gripper(direction, which_gripper):
    global left_gripper_rotation
    global right_gripper_rotation

    rotation_step = 0.205
    
    g = FollowJointTrajectoryGoal()
    g.trajectory = JointTrajectory()
    
    LEFT_ARM_JOINT_NAMES = ['l_ur5_arm_shoulder_pan_joint', 'l_ur5_arm_shoulder_lift_joint', 'l_ur5_arm_elbow_joint', 'l_ur5_arm_wrist_1_joint', 'l_ur5_arm_wrist_2_joint', 'l_ur5_arm_wrist_3_joint']
    RIGHT_ARM_JOINT_NAMES = ['r_ur5_arm_shoulder_pan_joint', 'r_ur5_arm_shoulder_lift_joint', 'r_ur5_arm_elbow_joint', 'r_ur5_arm_wrist_1_joint', 'r_ur5_arm_wrist_2_joint', 'r_ur5_arm_wrist_3_joint']
    
    if which_gripper is "left":
        g.trajectory.joint_names = LEFT_ARM_JOINT_NAMES
    if which_gripper is "right":
        g.trajectory.joint_names = RIGHT_ARM_JOINT_NAMES
    

    global interpreter
    current_group = interpreter.get_active_group()
    joints = current_group.get_current_joint_values()
    old_joints = joints
    rospy.loginfo(joints)
    global left_arm_client
    global right_arm_client

    # use the direction to move the joint value up or down. it's in radians. so should always figure itself out? or maybe needed to be bounded?
    if direction is "rotate_left":
        # Decrease the joint position in radians.
        val = joints[5]
        val += abs(rotation_step)
        joints[5] = val    
    if direction is "rotate_right":
        val = joints[5]
        val = val - abs(rotation_step)
        joints[5] = val


    if direction is "pan_left":
        rospy.loginfo("TODO")
    if direction is "pan_right":
        rospy.loginfo("TODO")
    if direction is "pan_up":
        rospy.loginfo("TODO")
    if direction is "pan_down":
        rospy.loginfo("TODO")

    current_group.set_joint_value_target(joints)
    current_group.go()

    return True

def joy_callback(msg):
    axes = msg.axes
    buttons = msg.buttons
    global left_arm
    global right_arm
    global left_gripper_closed
    global right_gripper_closed
    global gripper_cmd
    global gripper_mode
    global ptu_mode

    dx = 0.1
    # Dont do anything if the joy command is set to drive.
    if (buttons[0] > 0) or (buttons[2] > 0):
        return False

    if buttons[6]:
        # stow arms
        move_home()

    # Changing arm control modes. Only one arm controlled at a time.
    if axes[2] < 0:
        interpreter.execute("use left_arm")
        left_arm = True
        right_arm = False
        rospy.loginfo("MODE: LEFT ARM CONTROL MODE")
        return True
    if axes[5] < 0:
        interpreter.execute("use right_arm")
        right_arm = True
        left_arm = False
        rospy.loginfo("MODE: RIGHT ARM CONTROL MODE")
        return True
    # Left trigger pressed, send gripper close
    if buttons[4]:
        if left_gripper_closed:
            open_gripper = genCommand("o", gripper_cmd)
            gripper_publisher.publish(open_gripper)
            rospy.sleep(2)
            rospy.loginfo("Opening left gripper")
            left_gripper_closed = False
        else:
            close_gripper = genCommand("c", gripper_cmd)
            gripper_publisher.publish(close_gripper)
            rospy.sleep(2)
            left_gripper_closed = True
            rospy.loginfo("Closing left gripper")
        return True
    if buttons[5]:
        if right_gripper_closed:
            rospy.loginfo("Opening right gripper")
        else:
            rospy.loginfo("Closing right gripper")
        return True
    if buttons[1]:
        if not gripper_mode:
            gripper_mode = True
        else:
            gripper_mode = False

    left_joy_up = axes[1] > 0
    left_joy_down = axes[1] < 0
    left_joy_left = axes[0] > 0
    left_joy_right = axes[0] < 0

    left_joy_directions = [left_joy_up, left_joy_down, left_joy_left, left_joy_right]

    right_joy_up = axes[4] > 0
    right_joy_down = axes[4] < 0
    right_joy_left = axes[3] > 0
    right_joy_right = axes[3] < 0

    right_joystick_pressed = (buttons[10] == 1)
     

    # Check if LT is pressed
    if left_arm and not gripper_mode:
        # Left arm is pressed.
        if right_joystick_pressed:
            orient_gripper(left_joy_directions)
            return True
        elif left_joy_up:
            move_arm("forward", dx)
        elif left_joy_down:
            move_arm("back", dx)
        elif left_joy_left:
            move_arm("left", dx)
        elif left_joy_right:
            move_arm("right", dx)
        elif right_joy_up:
            move_arm("up", dx)
        elif right_joy_down:
            move_arm("down", dx)
    elif right_arm and not gripper_mode:
        # Right arm is pressed
        if left_joy_up:
            move_arm("forward", dx)
        if left_joy_down:
            move_arm("back", dx)
        if left_joy_left:
            move_arm("left", dx)
        if left_joy_right:
            move_arm("right", dx)
        if right_joy_up:
            move_arm("up", dx)
        if right_joy_down:
            move_arm("down", dx)
    elif gripper_mode:
        arm = ""
        if left_arm:
            arm = "left"
        elif right_arm:
            arm = "right"

        if left_joy_left:
            go_to_predefined(GRAB_OUT)
        elif left_joy_right:
            go_to_predefined(GRAB_IN)
        elif left_joy_up:
            rotate_gripper(GRAB_ABOVE)
        elif left_joy_down:
            rotate_gripper(GRAB_BELOW)
        elif right_joy_left:
            rotate_gripper("rotate_left", arm)
        elif right_joy_right:
            rotate_gripper("rotate_right", arm)
    elif ptu_mode:
        return True
 
def move_arm(direction, distance):
    global interpreter
    rospy.loginfo("Moving right arm " + direction + " " + str(distance))
    interpreter.execute("go " + direction + " " + str(distance))

if __name__=='__main__':

    roscpp_initialize(sys.argv)
    rospy.init_node('moveit_py_demo', anonymous=True)
    rospy.Subscriber("/joy_teleop/joy", Joy, joy_callback, queue_size=1)    

    #scene = PlanningSceneInterface()
    #robot = RobotCommander()
    #rospy.sleep(1)

    #left_arm = robot.left_arm
    #left_arm.go()
    global interpreter
    interpreter = MoveGroupCommandInterpreter()
    interpreter.execute("use left_arm")

    global gripper_publisher
    global gripper_cmd

    global left_arm_client
    global right_arm_client
   
    gripper_publisher = rospy.Publisher("/SModelRobotOutput", SModelRobotOutput)
    gripper_cmd = SModelRobotOutput()
    gripper_cmd = genCommand("a", gripper_cmd)

    left_arm_client = actionlib.SimpleActionClient('/l_arm_controller/follow_joint_trajectory', FollowJointTrajectoryAction)
    right_arm_client = actionlib.SimpleActionClient('/r_arm_controller/follow_joint_trajectory', FollowJointTrajectoryAction)
    rospy.loginfo("Waiting for left arm action server")
    left_arm_client.wait_for_server()
    rospy.loginfo("Waiting for right arm action server")
    right_arm_client.wait_for_server()
    rospy.loginfo("Connected to arm action servers")
    
    rospy.spin()
