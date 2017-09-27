#!/usr/bin/env python

import rospy,sys,roslib
from master_node.srv import *
from geometry_msgs.msg import Twist,Vector3

# define variables
avoidingVehicle = False
stopDetected=False
semaphoreDetected=False
twistmessage = 	Twist()
controlPub = rospy.Publisher("cmd_vel", Twist, queue_size=10)

def setMotorOff():
	global twistmessage
	twistmessage.linear.x = 0
	twistmessage.linear.y = 0
	twistmessage.linear.z = 0
	twistmessage.angular.x = 0
	twistmessage.angular.y = 0
	twistmessage.angular.z = 0

def semaphoreFunction(req):
	rospy.loginfo("SemaphoreService received infos")
	global semaphoreDetected
	if req.data.linear.x == 1: # Found a RED Trafficlight
		semaphoreDetected == True
	else: # Previous RED Trafficlight turned off
		semaphoreDetected == False
	return SemaphoreServiceResponse(bool(True))
	#TODO: Handle priority (this function doesn't turn off the motors)

def stopFunction(req):
	rospy.loginfo("StopService received infos")
	global stopDetected, twistmessage
	if req.data.linear.x == 0:
		rospy.loginfo("StopService received stop message")
		if twistmessage.linear.x > 0 and twistmessage.linear.y > 0:
			stopDetected = True
			setMotorOff()
	else:
		rospy.loginfo("StopService received go message")
		stopDetected = False
	controlPub.publish(twistmessage)
	return StopServiceResponse(bool(True))

def followFunction(data):
	global stopDetected, twistmessage
	if stopDetected is True:
		if data.linear.x < 0 and data.linear.y < 0:
			twistmessage = data
		else:
			setMotorOff()
	else:
		twistmessage = data
	controlPub.publish(twistmessage)

def master():
	# iniatilize twist values to 0
	setMotorOff()
	# initialize ros node
	rospy.init_node('master_node')
	stop_service = rospy.Service('stop',StopService,stopFunction)
	semaphore_service = rospy.Service('semaphore',SemaphoreService,semaphoreFunction)
	rospy.Subscriber("follow_topic",Twist,followFunction)
	rospy.loginfo("Master ready")
	try:
		rospy.spin()
	except KeyboardInterrupt:
		print("Shutting down")

if __name__=="__main__":
	try:
		master()
	except rospy.ROSInterruptException:
		pass
