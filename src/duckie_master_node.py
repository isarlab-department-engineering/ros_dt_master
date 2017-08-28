#!/usr/bin/env python

import rospy,sys,roslib
from master_node.srv import *
from geometry_msgs.msg import Twist,Vector3

# define variables
avoidingVehicle = False
twistmessage = 	Twist()
controlPub = rospy.Publisher("cmd_vel", Twist, queue_size=10)

def setMotorOff():
	twistmessage.linear.x = 0
	twistmessage.linear.y = 0
	twistmessage.linear.z = 0
	twistmessage.angular.x = 0
	twistmessage.angular.y = 0
	twistmessage.angular.z = 0

def stopFunction(data):
	print("ok")
	# twistmessahe = data
	# controlPub.publish(twistmessage)
	return StopServiceResponse(bool(True))

def followFunction(data):
	twistmessage = data
	controlPub.publish(twistmessage)

def master():
	# iniatilize twist values to 0
	setMotorOff()
	# initialize ros node
	rospy.init_node('master_node')
	stop_service = rospy.Service('stop',StopService,stopFunction)
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
