import cv2
from cv_bridge import CvBridge, CvBridgeError
import numpy as np
from genesis_msgs.msg import ESRTrackReport
from genesis_msgs.msg import MandoObjectReport
import rospy
from sensor_msgs.msg import Image
import matplotlib.pyplot as plt
import math
from jsk_recognition_msgs.msg import BoundingBoxArray
from jsk_recognition_msgs.msg import BoundingBox
from autoware_msgs.msg import image_obj
from genesis_msgs.msg import target
from genesis_msgs.msg import Multi_targets

pub_ped = rospy.Publisher('ped_bb', BoundingBoxArray, queue_size=2)
pub_car = rospy.Publisher('car_bb', BoundingBoxArray, queue_size=2)
pub_follow = rospy.Publisher('follow', BoundingBoxArray, queue_size=2)
pub_yolo = rospy.Publisher('yolo_bb',  BoundingBoxArray, queue_size=2)

pub_ly_fuse = rospy.Publisher('ly_fuse', Multi_targets, queue_size=2)
pub_leadc = rospy.Publisher('lead_car', BoundingBoxArray, queue_size=2)


pub_img_proc = rospy.Publisher("/image_yolo", Image, queue_size=2)

# Global varaibles
img = None; img_lock = False; img_tm = None
fx = 2346; cx = 644; #Camera Calibration
lidar_array = Multi_targets()
filter_boxes = BoundingBoxArray()

#### IS THIS CORRECT ?
#pre_box  =
#pre2_box  =
#pre3_box  =
#####

def img_callback(msg):
	# Maybe downsample?
	global img, img_tm, img_lock
	if img_lock == False:
		try:
			img = CvBridge().imgmsg_to_cv2(msg, "bgr8")
			img_tm = msg.header.stamp.secs + 1e-9 * msg.header.stamp.nsecs
		except CvBridgeError as e:
			print e

def LeadCarUpdate(msg):
	global lidar_array, filter_boxes
	leadc_boxes = BoundingBoxArray()
	leadc_boxes.header = filter_boxes.header
	compare_boxes = BoundingBoxArray()
	compare_boxes.header = filter_boxes.header
	compare_boxes.boxes = filter_boxes.boxes[:]

	if len(msg.data)==0:
		print('no lead car')
	else:
		rc_x = msg.data[0].pos_x
		rc_y = msg.data[0].pos_y
		rc_v = msg.data[0].speed

	distances = []
	for i in range(len(compare_boxes.boxes)):
		lidar_x = compare_boxes.boxes[i].pose.position.x
		lidar_y = compare_boxes.boxes[i].pose.position.y

		distance = np.sqrt((rc_x-lidar_x)**2+(rc_y-lidar_y)**2)
		distances.append(distance)
	print(min(distances))
	if (min(distances)<5):
		obj_i = distances.index(min(distances))
		leadc_boxes.boxes.append(compare_boxes.boxes[obj_i])
	else:
		leadc_box = BoundingBox()
		leadc_box.header = filter_boxes.boxes[1].header
		leadc_box.pose.position.x = rc_x
		leadc_box.pose.position.y = rc_y
		leadc_box.pose.position.z = .5
		leadc_box.pose.orientation.x = 0
		leadc_box.pose.orientation.y = 0
		leadc_box.pose.orientation.z = 0
		leadc_box.pose.orientation.w = 0
		leadc_box.dimensions.x = 5
		leadc_box.dimensions.y = 5
		leadc_box.dimensions.z = 5

		leadc_boxes.boxes.append(leadc_box)

	pub_leadc.publish(leadc_boxes)

# def parseYoloBoxes(msg):
# 	global img, img_lock, lidar_array, fx, cx, filter_boxes
# 	ly_array = Multi_targets()
# 	yolo_boxes = BoundingBoxArray()
# 	ly_array.data = lidar_array.data[:]
# 	yolo_boxes.header = filter_boxes.header
# 	#global yolobox
# 	#print 2
# 	#print data.obj.x
# 	#pubbox.publish(yolo_box)
# 	if len(msg.obj) > 0:
# 		# print msg.header.stamp.secs + 1e-9 * msg.header.stamp.nsecs
#
# 		img_local = None
# 		# copy the image, get the lock
# 		if (img is not None) and (img_lock == False):
# 			img_lock = True
# 			img_local = np.copy(img)
# 			img_lock = False
# 		else:
# 			print 'Waiting for image.'
#
#
# 		# overlay the boxes on the image and publish
# 		if img_local is not None:
# 			color = (0,0,0)
# 		 	if msg.type == 'person':
# 				color = (255,0,0)
# 			else:
# 				color = (0,0,255)
#
# 			for obj in msg.obj:
# 				yolo_t = target()
# 				x = obj.xprint(len(filter_boxes.boxes))
# 				y = obj.y
# 				w = obj.width
# 				h = obj.height
# 				s = obj.score
# 				# yolo_t.pos_x = x
# 				# yolo_t.pos_y = y
# 				# yolo_t.counter = s
# 				# if msg.type == 'person':
# 				# 	yolo_t.category = 0
# 				# else:	print(len(distances))
# 				# 	yolo_t.category = 1
#
# 				#calculate yolo angle
# 				yolo_angle = np.arctan(fx/((x+w/2)-cx))
# 				if yolo_angle < 0:
# 					yolo_angle = yolo_angle + 3.1415
# 				ly_angles = []
#
# 				#find the angle diff with every object in ly_array
# 				for i in range(len(ly_array.data)):
# 					ly_x = ly_array.data[i].pos_x
# 					ly_y = ly_array.data[i].pos_y
# 					ly_angle = np.arctan(ly_y/ly_x)
# 					if ly_angle < 0:
# 						ly_angle = ly_angle + 3.1415
# 					ly_angles.append(ly_angle)
# 				ly_angle_diff = [abs(angle - yolo_angle) for angle in ly_angles]
#
# 				# replace label for nearest object within 3 degrees and counter less that .25
# 				# update score
# 				obj_i = ly_angle_diff.index(min(ly_angle_diff))
# 				if (min(ly_angle_diff)<0.1):
# 					if msg.type=='person':
# 						ly_array.data[obj_i].category = 1
# 						yolo_boxes.boxes.append(filter_boxes.boxes[obj_i])
# 					# else:
# 					# 	lidar_array.data[obj_i].category = 2
# 						ly_array.data[obj_i].counter = s
#
# 				# print 'typearray: %s, xnts_no_ground: %d, y: %d, h: %d, w: %d, score: %f\n' % (msg.type,x,y,h,w,s)
# 				cv2.rectangle(img_local, (x,y), (x+w, y+h),color = color , thickness = 3)
# 			img_msg = CvBridge().cv2_to_imgmsg(img_local, encoding="bgr8")
# 			pub_img_proc.publish(img_msg)
# 		pub_yolo.publish(yolo_boxes)
# 		pub_ly_fuse.publish(ly_array)

def parseBoxes(data):
	global lidar_array
	global filter_boxes
	filter_boxes = BoundingBoxArray()
	data_ped = BoundingBoxArray()
	data_car = BoundingBoxArray()
	data_follow = BoundingBoxArray()  # What is that ?

	previous_targets = BoundingBoxArray()	#WE NEED TO INITIALIZE IT


	data_ped.header = data.header
	data_car.header = data.header
	data_follow.header = data.header
	filter_boxes.header = data.header
	lidar_array = Multi_targets()

	data_copy = data # We do that to be able to modify time stamp. Does it work ?
#Remove flickering loop

	for i in range(len(data.boxes)):

		x = data_copy.boxes[i].pose.position.x
		y = data_copy.boxes[i].pose.position.y

		for j in range(len(previous_targets)):
			x_previous = previous_targets.boxes[j].pose.position.x
			y_previous = previous_targets.boxes[j].pose.position.y

			distance = math.sqrt( (x - x_previous)**2 +  (y - y_previous)**2 )

			# WE CAN ALSO COMPARE THE BOX SIZE

			if distance < 0.25:
				 = data_copy.boxes[i].header.stamp.secs




for i in range(len(data.boxes)):
		lidar_target = target()
		x = data.boxes[i].pose.position.x
		y = data.boxes[i].pose.position.y
		height = data.boxes[i].dimensions.z
		length = data.boxes[i].dimensions.x
		width = data.boxes[i].dimensions.y
		lidar_target.pos_x = x
		lidar_target.pos_y = y

		print data.boxes[i]


		# If the target is in front of the car
		if (y<50 and y>0) and (x<2.5 and x>-2.5):
			data_follow.boxes.append(data.boxes[i])

		# If the target is in front of the car (or slightly behind)
		if (y<50 and y>-10) and (x<8 and x>-12):
			height = data.boxes[i].dimensions.z
			length = data.boxes[i].dimensions.x
			width = data.boxes[i].dimensions.y

			# It's a Pedestrian
			if (height < 1.8 and height > 0.5) and (length < 1.5 and length > 0) and (width < 1.5 and width > 0):
				data_ped.boxes.append(data.boxes[i])
				# lidar_target.category = 0
				# lidar_target.counter = .1

			# It's a Vehicle
			elif (height < 5 and height > 0.5) and (length < 10 and length > 0) and (width < 10 and width > 0):

		# If the target is in front of the car
		if (y<50 and y>0) and (x<2.5 and x>-2.5):
			data_follow.boxes.append(data.boxes[i])

		# If the target is in front of the car (or slightly behind)
		if (y<50 and y>-10) and (x<8 and x>-12):
			height = data.boxes[i].dimensions.zBoundingBoxArray
			length = data.boxes[i].dimensions.x
			width = data.boxes[i].dimensions.y

			# It's a Pedestrian
			if (height < 1.8 and height > 0.5) and (length < 1.5 and length > 0) and (width < 1.5 and width > 0):
				data_ped.boxes.append(data.boxes[i])
				# lidar_target.category = 0
				# lidar_target.counter = .1

			# It's a Vehicle2
			elif (height < 5 and height > 0.5) and (length < 10 and length > 0) and (width < 10 and width > 0):


								data_car.boxes.append(data.boxes[i])
				# lidar_target.category = 1
				# lidar_target.counter = .1
			lidar_array.datafor i in range(len(data.boxes)):
		lidar_target = target()
		x = data.boxes[i].pose.position.x
		y = data.boxes[i].pose.position.y
		height = data.boxes[i].dimensions.z
		length = data.boxes[i].dimensions.x
		width = data.boxes[i].dimensions.y
		lidar_target.pos_x = x
		lidar_target.pos_y = y

		print data.boxes[i]


		# If the target is in front of the car
		if (y<50 and y>0) and (x<2.5 and x>-2.5):
			data_follow.boxes.append(data.boxes[i])

		# If the target is in front of the car (or slightly behind)
		if (y<50 and y>-10) and (x<8 and x>-12):
			height = data.boxes[i].dimensions.z
			length = data.boxes[i].dimensions.x
			width = data.boxes[i].dimensions.y

			# It's a Pedestrian
			if (height < 1.8 and height > 0.5) and (length < 1.5 and length > 0) and (width < 1.5 and width > 0):
				data_ped.boxes.append(data.boxes[i])
				# lidar_target.category = 0
				# lidar_target.counter = .1

			# It's a Vehicle
			elif (height < 5 and height > 0.5) and (length < 10 and length > 0) and (width < 10 and width > 0):
.append(lidar_target)
			filter_boxes.boxes.append(data.boxes[i])




	pub_ped.publish(data_ped)
	pub_car.publish(data_car)
	pub_follow.publish(data_follow)


def radar_draw_loop():
	rospy.init_node('lidar_box_filter', anonymous = True)

	# Lidar subscriber
	rospy.Subscriber('/bounding_boxes', BoundingBoxArray, parseBoxes, queue_size = 2)

	# Yolo subscribers
	rospy.init_node('lidar_box_filter', anonymous = True)
	# sub_person = rospy.Subscriber('/obj_person/image_obj', image_obj, parseYoloBoxes, queue_size = 2)
	# sub_car = rospy.Subscriber('/obj_car/image_obj', image_obj, parseYoloBoxes, queue_size = 2)
	sub_img = rospy.Subscriber("/image_raw", Image, img_callback, queue_size=2)

	# radar lead car subscriber
	rospy.Subscriber('/radar_targets_acc', Multi_targets, LeadCarUpdate, queue_size = 2)

	rospy.spin()
if __name__=='__main__':
	radar_draw_loop()
