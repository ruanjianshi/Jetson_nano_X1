; Auto-generated. Do not edit!


(cl:in-package maita_can_comm-msg)


;//! \htmlinclude CANCommGoal.msg.html

(cl:defclass <CANCommGoal> (roslisp-msg-protocol:ros-message)
  ((can_id
    :reader can_id
    :initarg :can_id
    :type cl:integer
    :initform 0)
   (data
    :reader data
    :initarg :data
    :type (cl:vector cl:fixnum)
   :initform (cl:make-array 0 :element-type 'cl:fixnum :initial-element 0))
   (dlc
    :reader dlc
    :initarg :dlc
    :type cl:fixnum
    :initform 0)
   (extended
    :reader extended
    :initarg :extended
    :type cl:boolean
    :initform cl:nil)
   (channel
    :reader channel
    :initarg :channel
    :type cl:integer
    :initform 0))
)

(cl:defclass CANCommGoal (<CANCommGoal>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <CANCommGoal>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'CANCommGoal)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name maita_can_comm-msg:<CANCommGoal> is deprecated: use maita_can_comm-msg:CANCommGoal instead.")))

(cl:ensure-generic-function 'can_id-val :lambda-list '(m))
(cl:defmethod can_id-val ((m <CANCommGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:can_id-val is deprecated.  Use maita_can_comm-msg:can_id instead.")
  (can_id m))

(cl:ensure-generic-function 'data-val :lambda-list '(m))
(cl:defmethod data-val ((m <CANCommGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:data-val is deprecated.  Use maita_can_comm-msg:data instead.")
  (data m))

(cl:ensure-generic-function 'dlc-val :lambda-list '(m))
(cl:defmethod dlc-val ((m <CANCommGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:dlc-val is deprecated.  Use maita_can_comm-msg:dlc instead.")
  (dlc m))

(cl:ensure-generic-function 'extended-val :lambda-list '(m))
(cl:defmethod extended-val ((m <CANCommGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:extended-val is deprecated.  Use maita_can_comm-msg:extended instead.")
  (extended m))

(cl:ensure-generic-function 'channel-val :lambda-list '(m))
(cl:defmethod channel-val ((m <CANCommGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:channel-val is deprecated.  Use maita_can_comm-msg:channel instead.")
  (channel m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <CANCommGoal>) ostream)
  "Serializes a message object of type '<CANCommGoal>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'can_id)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'can_id)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'can_id)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'can_id)) ostream)
  (cl:let ((__ros_arr_len (cl:length (cl:slot-value msg 'data))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_arr_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_arr_len) ostream))
  (cl:map cl:nil #'(cl:lambda (ele) (cl:write-byte (cl:ldb (cl:byte 8 0) ele) ostream))
   (cl:slot-value msg 'data))
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'dlc)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'extended) 1 0)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'channel)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'channel)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'channel)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'channel)) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <CANCommGoal>) istream)
  "Deserializes a message object of type '<CANCommGoal>"
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'can_id)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'can_id)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'can_id)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'can_id)) (cl:read-byte istream))
  (cl:let ((__ros_arr_len 0))
    (cl:setf (cl:ldb (cl:byte 8 0) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) __ros_arr_len) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) __ros_arr_len) (cl:read-byte istream))
  (cl:setf (cl:slot-value msg 'data) (cl:make-array __ros_arr_len))
  (cl:let ((vals (cl:slot-value msg 'data)))
    (cl:dotimes (i __ros_arr_len)
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:aref vals i)) (cl:read-byte istream)))))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'dlc)) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'extended) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'channel)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'channel)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'channel)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'channel)) (cl:read-byte istream))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<CANCommGoal>)))
  "Returns string type for a message object of type '<CANCommGoal>"
  "maita_can_comm/CANCommGoal")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'CANCommGoal)))
  "Returns string type for a message object of type 'CANCommGoal"
  "maita_can_comm/CANCommGoal")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<CANCommGoal>)))
  "Returns md5sum for a message object of type '<CANCommGoal>"
  "2132a7b42d5791ec0695a2dd6adc00dc")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'CANCommGoal)))
  "Returns md5sum for a message object of type 'CANCommGoal"
  "2132a7b42d5791ec0695a2dd6adc00dc")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<CANCommGoal>)))
  "Returns full string definition for message of type '<CANCommGoal>"
  (cl:format cl:nil "# ====== DO NOT MODIFY! AUTOGENERATED FROM AN ACTION DEFINITION ======~%# goal definition~%uint32 can_id           # CAN帧ID~%uint8[] data            # CAN数据 (最多8字节)~%uint8 dlc               # 数据长度 (0-8)~%bool extended           # 是否使用扩展帧~%uint32 channel          # CAN通道 (0=CAN0, 1=CAN1)~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'CANCommGoal)))
  "Returns full string definition for message of type 'CANCommGoal"
  (cl:format cl:nil "# ====== DO NOT MODIFY! AUTOGENERATED FROM AN ACTION DEFINITION ======~%# goal definition~%uint32 can_id           # CAN帧ID~%uint8[] data            # CAN数据 (最多8字节)~%uint8 dlc               # 数据长度 (0-8)~%bool extended           # 是否使用扩展帧~%uint32 channel          # CAN通道 (0=CAN0, 1=CAN1)~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <CANCommGoal>))
  (cl:+ 0
     4
     4 (cl:reduce #'cl:+ (cl:slot-value msg 'data) :key #'(cl:lambda (ele) (cl:declare (cl:ignorable ele)) (cl:+ 1)))
     1
     1
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <CANCommGoal>))
  "Converts a ROS message object to a list"
  (cl:list 'CANCommGoal
    (cl:cons ':can_id (can_id msg))
    (cl:cons ':data (data msg))
    (cl:cons ':dlc (dlc msg))
    (cl:cons ':extended (extended msg))
    (cl:cons ':channel (channel msg))
))
