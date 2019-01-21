#!/usr/bin/env python

import rospy,sys,roslib
import time as t
#import queue
#from multiprocessing import Queue
from Queue import PriorityQueue
from master_node.srv import *
from geometry_msgs.msg import Twist,Vector3
from master_node.msg import *

#define priority list
priority_dict = {'aruco':3, 'lane':2, 'joy':1}


#define priority queue
priority_queue = PriorityQueue()


# define variables
id_in_lock = None
avoidingVehicle = False
stopDetected=False
semaphoreDetected=False
twistmessage = 	Twist()
lock_msg = Lock()
timeDetected = t.time()
controlPub = rospy.Publisher("cmd_vel", Twist, queue_size=10)
lockPub = rospy.Publisher("lock_shared", Lock, queue_size=10)


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
	global stopDetected, twistmessage, timeDetected
	timeDetected = t.time()
	ducks_founded = req.ducks_founded
	stopDetected = True
	#setMotorOff()
	#rospy.loginfo("Motors Stopped, founded "+ducks_founded+" Ducks")
	return StopServiceResponse(bool(True))

def requestLockFunction(req):
	
	global id_in_lock, priority_dict, priority_queue, lock_msg
	ack = False
	id_node = req.id
	rospy.loginfo("RequestLockService received infos ["+id_node+"]")
	priority_node = priority_dict[id_node]
	if id_in_lock is None:
		id_in_lock = id_node
		ack = True
		rospy.loginfo("Lock assegnato a ["+id_node+"]")
	else:
		priority_in_lock = priority_dict[id_in_lock]
		if priority_node > priority_in_lock:
			priority_queue.put((priority_node,id_node))
			rospy.loginfo("Messo in coda ["+id_node+"]")
		else:
			#informa il nodo che ha il lock di averlo perso, pubblicando sul topic shared
			
			lock_msg.id = id_in_lock
			lock_msg.msg = 2
			lockPub.publish(lock_msg)
			rospy.loginfo("informo ["+id_in_lock+"] che ha perso il lock")

			#Aggiorna il nodo che ora ha il lock
			id_in_lock = id_node
			ack=True

	rospy.loginfo("Ack mandato a ["+id_node+"] = "+str(ack))
	return RequestLockServiceResponse(bool(ack))


def releaseLockFunction(req):
	rospy.loginfo("ReleaseLockService received infos")
	global id_in_lock, priority_dict, priority_queue, lock_msg
	if not priority_queue.empty():
		next_node = priority_queue.get()
		id_in_lock = next_node[1]

		#informa il nodo che ha ottenuto il lock e puo 'risvegliarsi', pubblicando su un topic shared
		lock_msg.id = id_in_lock
		lock_msg.msg = 1
		lockPub.publish(lock_msg)


	else:
		id_in_lock = None

	return ReleaseLockServiceResponse(bool(True))



def followFunction(data):
	global stopDetected, twistmessage, timeDetected
	now = t.time()
	id_node = data.id
	twist = data.twist
	if id_node == id_in_lock:
		if stopDetected is True:
		    if (now - timeDetected) > 1:
			stopDetected = False
		    else:
			setMotorOff()
		else:
			twistmessage = twist
		controlPub.publish(twistmessage)
	else:
		pass
		#rospy.loginfo("Detected message without lock ["+id_node+"]")

def master():
	# iniatilize twist values to 0
	setMotorOff()
	# initialize ros node
	rospy.init_node('master_node')
	stop_service = rospy.Service('stop',StopService,stopFunction)
	semaphore_service = rospy.Service('semaphore',SemaphoreService,semaphoreFunction)
	request_lock_service = rospy.Service('request_lock',RequestLockService,requestLockFunction)
	release_lock_service = rospy.Service('release_lock',ReleaseLockService,releaseLockFunction)


	rospy.Subscriber("follow_topic",Follow,followFunction)
	#fare in modo che il master ignori i messaggi di chi non ha il lock (con un messaggio diverso?)

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