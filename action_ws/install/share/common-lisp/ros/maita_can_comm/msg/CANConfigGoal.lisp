; Auto-generated. Do not edit!


(cl:in-package maita_can_comm-msg)


;//! \htmlinclude CANConfigGoal.msg.html

(cl:defclass <CANConfigGoal> (roslisp-msg-protocol:ros-message)
  ((channel
    :reader channel
    :initarg :channel
    :type cl:integer
    :initform 0)
   (baudrate
    :reader baudrate
    :initarg :baudrate
    :type cl:integer
    :initform 0)
   (enable_loopback
    :reader enable_loopback
    :initarg :enable_loopback
    :type cl:boolean
    :initform cl:nil)
   (enable_timestamp
    :reader enable_timestamp
    :initarg :enable_timestamp
    :type cl:boolean
    :initform cl:nil))
)

(cl:defclass CANConfigGoal (<CANConfigGoal>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <CANConfigGoal>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'CANConfigGoal)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name maita_can_comm-msg:<CANConfigGoal> is deprecated: use maita_can_comm-msg:CANConfigGoal instead.")))

(cl:ensure-generic-function 'channel-val :lambda-list '(m))
(cl:defmethod channel-val ((m <CANConfigGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:channel-val is deprecated.  Use maita_can_comm-msg:channel instead.")
  (channel m))

(cl:ensure-generic-function 'baudrate-val :lambda-list '(m))
(cl:defmethod baudrate-val ((m <CANConfigGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:baudrate-val is deprecated.  Use maita_can_comm-msg:baudrate instead.")
  (baudrate m))

(cl:ensure-generic-function 'enable_loopback-val :lambda-list '(m))
(cl:defmethod enable_loopback-val ((m <CANConfigGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:enable_loopback-val is deprecated.  Use maita_can_comm-msg:enable_loopback instead.")
  (enable_loopback m))

(cl:ensure-generic-function 'enable_timestamp-val :lambda-list '(m))
(cl:defmethod enable_timestamp-val ((m <CANConfigGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader maita_can_comm-msg:enable_timestamp-val is deprecated.  Use maita_can_comm-msg:enable_timestamp instead.")
  (enable_timestamp m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <CANConfigGoal>) ostream)
  "Serializes a message object of type '<CANConfigGoal>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'channel)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'channel)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'channel)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'channel)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'baudrate)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'baudrate)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'baudrate)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'baudrate)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'enable_loopback) 1 0)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'enable_timestamp) 1 0)) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <CANConfigGoal>) istream)
  "Deserializes a message object of type '<CANConfigGoal>"
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'channel)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'channel)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'channel)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'channel)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'baudrate)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'baudrate)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'baudrate)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'baudrate)) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'enable_loopback) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:setf (cl:slot-value msg 'enable_timestamp) (cl:not (cl:zerop (cl:read-byte istream))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<CANConfigGoal>)))
  "Returns string type for a message object of type '<CANConfigGoal>"
  "maita_can_comm/CANConfigGoal")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'CANConfigGoal)))
  "Returns string type for a message object of type 'CANConfigGoal"
  "maita_can_comm/CANConfigGoal")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<CANConfigGoal>)))
  "Returns md5sum for a message object of type '<CANConfigGoal>"
  "3dc91cac39863340c8f462fe7adc795f")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'CANConfigGoal)))
  "Returns md5sum for a message object of type 'CANConfigGoal"
  "3dc91cac39863340c8f462fe7adc795f")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<CANConfigGoal>)))
  "Returns full string definition for message of type '<CANConfigGoal>"
  (cl:format cl:nil "# ====== DO NOT MODIFY! AUTOGENERATED FROM AN ACTION DEFINITION ======~%# goal definition~%uint32 channel          # CAN通道 (0=CAN0, 1=CAN1)~%uint32 baudrate         # 波特率 (如: 500000)~%bool enable_loopback    # 启用回环模式~%bool enable_timestamp   # 启用时间戳~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'CANConfigGoal)))
  "Returns full string definition for message of type 'CANConfigGoal"
  (cl:format cl:nil "# ====== DO NOT MODIFY! AUTOGENERATED FROM AN ACTION DEFINITION ======~%# goal definition~%uint32 channel          # CAN通道 (0=CAN0, 1=CAN1)~%uint32 baudrate         # 波特率 (如: 500000)~%bool enable_loopback    # 启用回环模式~%bool enable_timestamp   # 启用时间戳~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <CANConfigGoal>))
  (cl:+ 0
     4
     4
     1
     1
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <CANConfigGoal>))
  "Converts a ROS message object to a list"
  (cl:list 'CANConfigGoal
    (cl:cons ':channel (channel msg))
    (cl:cons ':baudrate (baudrate msg))
    (cl:cons ':enable_loopback (enable_loopback msg))
    (cl:cons ':enable_timestamp (enable_timestamp msg))
))
