import rospy
import sys
import tf2_ros as tf2
import tf_conversions as tfc
import geometry_msgs.msg
from tf2_msgs.msg import TFMessage
import math
import numpy

def qRot(p, q):
    qInvert = tfc.transformations.quaternion_inverse
    qMultiply = tfc.transformations.quaternion_multiply
    qInv = qInvert(q)
    pNew = qMultiply(qMultiply(q, p), qInv)
    return pNew

def qRotInv(p, q):
    qInvert = tfc.transformations.quaternion_inverse
    qMultiply = tfc.transformations.quaternion_multiply
    qInv = qInvert(q)
    pNew = qMultiply(qMultiply(qInv, p), q)
    return pNew


def __genTf(frameT, frameS, posTs, q):
    ts = geometry_msgs.msg.TransformStamped()
    ts.header.stamp = rospy.Time.now()
    ts.header.frame_id = frameT
    ts.child_frame_id = frameS
    
    ts.transform.translation.x = posTs[0]
    ts.transform.translation.y = posTs[1]
    ts.transform.translation.z = posTs[2]

    ts.transform.rotation.x = q[0]
    ts.transform.rotation.y = q[1]
    ts.transform.rotation.z = q[2]
    ts.transform.rotation.w = q[3]
    return ts

def __main():
    rospy.init_node("A2C")
    rate = rospy.Rate(1)
    tbf = tf2.Buffer()
    tl = tf2.TransformListener(tbf)
    
    a = 0
    pp = 0
    while not tbf.can_transform("C", "D", rospy.Time()) and not rospy.is_shutdown():
        print "waiting for static tf ready.{C-D}"
        rate.sleep()
        
    while not tbf.can_transform("D", "C", rospy.Time()) and not rospy.is_shutdown():
        print "waiting for static tf ready.{D-C}"
        rate.sleep()
        
    while not tbf.can_transform("A", "B", rospy.Time()) and not rospy.is_shutdown():
        print "waiting for static tf ready.{A-B}"
        rate.sleep()
        
    while not tbf.can_transform("B", "A", rospy.Time()) and not rospy.is_shutdown():
        print "waiting for static tf ready.{B-A}"
        rate.sleep()
        
    print ("all static tf ready")
            
    roundCount = 0
    rateFast = rospy.Rate(10)
    
    qInvert = tfc.transformations.quaternion_inverse
    qMultiply = tfc.transformations.quaternion_multiply
    while not rospy.is_shutdown():
        print("begin: " + str(roundCount))
        roundCount += 1
        # lookup_transform(desFrame, srcFrame, time)
        tfD2C = tbf.lookup_transform("C", "D", rospy.Time())
        tfC2D = tbf.lookup_transform("D", "C", rospy.Time())
        tfB2A = tbf.lookup_transform("A", "B", rospy.Time())
        tfA2B = tbf.lookup_transform("B", "A", rospy.Time())
        
        bc = tf2.TransformBroadcaster()

        tD2B = (2 * math.cos(a), 1 + 2 * math.sin(a), -1, 0)
        qD2B = tfc.transformations.quaternion_from_euler(0, 0, math.pi / 2 + a)
        
        ts = __genTf("B", "DB", tD2B, qD2B)
        bc.sendTransform(ts)

        # db -> da
        tfm = tfB2A
        r = tfm.transform.rotation
        ts = tfm.transform.translation
        qB2A = numpy.array([r.x, r.y, r.z, r.w])
        tB2A = numpy.array([ts.x, ts.y, ts.z, 0])
        qD2A = qMultiply(qB2A, qD2B)
        tD2A = qRot(tD2B, qB2A)  + tB2A

        ts = __genTf("A", "DA", tD2A, qD2A)
        bc.sendTransform(ts)
        
        # da -> ca
        tfm = tfC2D
        r = tfm.transform.rotation
        ts = tfm.transform.translation
        qC2D = numpy.array([r.x, r.y, r.z, r.w])
        tC2D = numpy.array([ts.x, ts.y, ts.z, 0])
        qC2A = qMultiply(qD2A, qC2D)
        tC2A = qRot(tC2D, qD2A) + tD2A
        ts = __genTf("A", "C", tC2A, qC2A)
        bc.sendTransform(ts)

        if a < math.pi * 2:
            a += 0.01
        else:
            a = 0

        rateFast.sleep()


if __name__ == "__main__":
    __main() 