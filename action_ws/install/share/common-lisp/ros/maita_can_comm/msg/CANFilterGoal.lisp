; Auto-generated. Do not edit!


(cl:in-package maita_can_comm-msg)


;//! \htmlinclude CANFilterGoal.msg.html

(cl:defclass <CANFilterGoal> (roslisp-msg-protocol:ros-message)
  ((channel
    :reader channel
    :initarg :channel
    :type cl:integer
    :initform 0)
   (can_id
    :reader can_id
    :initarg :can_id
    :type cl:integer
    :initform 0)
   (can_id_mask
    :reader can_id_mask
    :initarg :can_id_mask
    :type cl:integer
    :initform 0)
   (enable
    :reader enable
    :initarg :enable
    :type cl:boolean
    :initform cl:nil)
   (extended
    :reader extended
    :initarg :extended
    :type cl:boolean
    :initform cl:nil))
)

(cl:defclass CANFilterGoal (<CANFilterGoal>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <CANFilterGoal>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'CANFilterGoal)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name maita_can_comm-msg:<CANFilterGoal> is deprecated: use maita_can_comm-msg:CANFilterGoal instead.")))

(cl:ensure-generic-function 'channel-val :lambda-list '(m))
(cl:defmethod channel-val ((m <CANFilterGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:channel-val is deprecated.  Use maita_can_comm-msg:channel instead.")
  (channel m))

(cl:ensure-generic-function 'can_id-val :lambda-list '(m))
(cl:defmethod can_id-val ((m <CANFilterGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:can_id-val is deprecated.  Use maita_can_comm-msg:can_id instead.")
  (can_id m))

(cl:ensure-generic-function 'can_id_mask-val :lambda-list '(m))
(cl:defmethod can_id_mask-val ((m <CANFilterGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:can_id_mask-val is deprecated.  Use maita_can_comm-msg:can_id_mask instead.")
  (can_id_mask m))

(cl:ensure-generic-function 'enable-val :lambda-list '(m))
(cl:defmethod enable-val ((m <CANFilterGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:enable-val is deprecated.  Use maita_can_comm-msg:enable instead.")
  (enable m))

(cl:ensure-generic-function 'extended-val :lambda-list '(m))
(cl:defmethod extended-val ((m <CANFilterGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:extended-val is deprecated.  Use maita_can_comm-msg:extended instead.")
  (extended m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <CANFilterGoal>) ostream)
  "Serializes a message object of type '<CANFilterGoal>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'channel)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'channel)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'channel)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'channel)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'can_id)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'can_id)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'can_id)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'can_id)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'can_id_mask)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'can_id_mask)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'can_id_mask)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'can_id_mask)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'enable) 1 0)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'extended) 1 0)) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <CANFilterGoal>) istream)
  "Deserializes a message object of type '<CANFilterGoal>"
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'channel)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'channel)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'channel)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'channel)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'can_id)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'can_id)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'can_id)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'can_id)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'can_id_mask)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'can_id_mask)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'can_id_mask)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'can_id_mask)) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'enable) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:setf (cl:slot-value msg 'extended) (cl:not (cl:zerop (cl:read-byte istream))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<CANFilterGoal>)))
  "Returns string type for a message object of type '<CANFilterGoal>"
  "maita_can_comm/CANFilterGoal")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'CANFilterGoal)))
  "Returns string type for a message object of type 'CANFilterGoal"
  "maita_can_comm/CANFilterGoal")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<CANFilterGoal>)))
  "Returns md5sum for a message object of type '<CANFilterGoal>"
  "22a569785d38997a7f1c42f98c5d9c20")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'CANFilterGoal)))
  "Returns md5sum for a message object of type 'CANFilterGoal"
  "22a569785d38997a7f1c42f98c5d9c20")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<CANFilterGoal>)))
  "Returns full string definition for message of type '<CANFilterGoal>"
  (cl:format cl:nil "# ====== DO NOT MODIFY! AUTOGENERATED FROM AN ACTION DEFINITION ======~%# goal definition~%uint32 channel          # CAN通道~%uint32 can_id           # CAN帧ID~%uint32 can_id_mask      # CAN帧ID掩码~%bool enable             # 启用过滤~%bool extended           # 扩展帧过滤~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'CANFilterGoal)))
  "Returns full string definition for message of type 'CANFilterGoal"
  (cl:format cl:nil "# ====== DO NOT MODIFY! AUTOGENERATED FROM AN ACTION DEFINITION ======~%# goal definition~%uint32 channel          # CAN通道~%uint32 can_id           # CAN帧ID~%uint32 can_id_mask      # CAN帧ID掩码~%bool enable             # 启用过滤~%bool extended           # 扩展帧过滤~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <CANFilterGoal>))
  (cl:+ 0
     4
     4
     4
     1
     1
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <CANFilterGoal>))
  "Converts a ROS message object to a list"
  (cl:list 'CANFilterGoal
    (cl:cons ':channel (channel msg))
    (cl:cons ':can_id (can_id msg))
    (cl:cons ':can_id_mask (can_id_mask msg))
    (cl:cons ':enable (enable msg))
    (cl:cons ':extended (extended msg))
))
