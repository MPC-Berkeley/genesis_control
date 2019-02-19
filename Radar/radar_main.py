import cv2
from cv_bridge import CvBridge, CvBridgeError
import numpy as np
from genesis_msgs.msg import ESRTrackReport
from genesis_msgs.msg import MandoObjectReport
import rospy
from sensor_msgs.msg import Image
import matplotlib.pyplot as plt
import math

img = None
radar = [dict() for i in range(64)]
objects = [dict() for i in range(8)]

def parseImg(msg):
	global img
	try:
		img = CvBridge().imgmsg_to_cv2(msg, "rgb8")		
	except CvBridgeError as e:
		print e

def parseRadar(msg):
	global radar

	index  = int(msg.header.frame_id) - 1
	status = msg.status # > 0 = valid target
	mode   = msg.mode   # > 0 = detected by either MR/LR
	dist   = msg.range
	vel    = msg.range_rate
	acc    = msg.range_accel
	angle  = msg.angle
	
	radar[index]['status'] = status
	radar[index]['mode'] = mode
	radar[index]['dist'] = dist
	radar[index]['vel'] = vel
	radar[index]['acc'] = acc
	radar[index]['angle'] = angle

def parseObject(msg):
	global objects

	index  = msg.index - 1
	obj_id  = msg.object_identifier # > 0 = a target
	valid   = msg.object_valid
	x      = msg.range
	y      = msg.position_y

	objects[index]['obj_id'] = obj_id
	objects[index]['valid'] = valid
	objects[index]['x'] = x
	objects[index]['y'] = y

def radar_draw_loop():
	rospy.init_node('radar_viz', anonymous = True)
	#rospy.Subscriber('/image_raw', Image, parseImg, queue_size = 2)
	rospy.Subscriber('/mando_radar/esr_track', ESRTrackReport, parseRadar, queue_size = 2)
	rospy.Subscriber('/mando_camera/object_detection', MandoObjectReport, parseObject, queue_size = 2)
	r = rospy.Rate(10.0)

	f, ax1 = plt.subplots(1)

	plt.ion()

	
	global img, radar
	while not rospy.is_shutdown():
		
		#if img is None:
			#print('Waiting: img')
			#r.sleep()
			#continue
		#img = cv2.resize(img, (224, 224), interpolation=cv2.INTER_AREA)
		#ax1.imshow(img)


		#ax2.clear()

		for i in range(64):
			if 'status' in radar[i].keys() and radar[i]['status'] > 0:
				
				heading  = -math.radians(radar[i]['angle']) + math.pi/2
				distance = radar[i]['dist']
				velocity = radar[i]['vel']

				obj_x = distance * math.cos(heading)
				obj_y = distance * math.sin(heading)
				#ax1.plot(obj_x, obj_y, 'rx', markersize=8)

				# ------------------------
				if velocity > 0.1:
					ax1.plot(obj_x, obj_y, 'rx', markersize=8)	
					print velocity
				# ------------------------

		#for i in range(8):
		#	if 'obj_id' in objects[i].keys() and objects[i]['obj_id'] > 0:

		#		x = objects[i]['x']
		#		y = objects[i]['y']
		#		valid = objects[i]['valid']

		#		if valid > 0:
		#			ax2.plot(x, y, 'kx', markersize=8)
		#		else:
		#			ax2.plot(x, y, 'gx', markersize=8)
		
		plt.xlim([-6, 6])
		plt.ylim([-1, 50])
		plt.grid()

		f.canvas.draw()
		
		plt.pause(0.001)
		r.sleep()

if __name__=='__main__':
	radar_draw_loop()