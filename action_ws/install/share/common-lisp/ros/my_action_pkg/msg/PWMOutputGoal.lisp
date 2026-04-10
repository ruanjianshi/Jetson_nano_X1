; Auto-generated. Do not edit!


(cl:in-package my_action_pkg-msg)


;//! \htmlinclude PWMOutputGoal.msg.html

(cl:defclass <PWMOutputGoal> (roslisp-msg-protocol:ros-message)
  ((pin_number
    :reader pin_number
    :initarg :pin_number
    :type cl:fixnum
    :initform 0)
   (frequency
    :reader frequency
    :initarg :frequency
    :type cl:integer
    :initform 0)
   (duty_cycle
    :reader duty_cycle
    :initarg :duty_cycle
    :type cl:fixnum
    :initform 0)
   (duration
    :reader duration
    :initarg :duration
    :type cl:float
    :initform 0.0))
)

(cl:defclass PWMOutputGoal (<PWMOutputGoal>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <PWMOutputGoal>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'PWMOutputGoal)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name my_action_pkg-msg:<PWMOutputGoal> is deprecated: use my_action_pkg-msg:PWMOutputGoal instead.")))

(cl:ensure-generic-function 'pin_number-val :lambda-list '(m))
(cl:defmethod pin_number-val ((m <PWMOutputGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader my_action_pkg-msg:pin_number-val is deprecated.  Use my_action_pkg-msg:pin_number instead.")
  (pin_number m))

(cl:ensure-generic-function 'frequency-val :lambda-list '(m))
(cl:defmethod frequency-val ((m <PWMOutputGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader my_action_pkg-msg:frequency-val is deprecated.  Use my_action_pkg-msg:frequency instead.")
  (frequency m))

(cl:ensure-generic-function 'duty_cycle-val :lambda-list '(m))
(cl:defmethod duty_cycle-val ((m <PWMOutputGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader my_action_pkg-msg:duty_cycle-val is deprecated.  Use my_action_pkg-msg:duty_cycle instead.")
  (duty_cycle m))

(cl:ensure-generic-function 'duration-val :lambda-list '(m))
(cl:defmethod duration-val ((m <PWMOutputGoal>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader my_action_pkg-msg:duration-val is deprecated.  Use my_action_pkg-msg:duration instead.")
  (duration m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <PWMOutputGoal>) ostream)
  "Serializes a message object of type '<PWMOutputGoal>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'pin_number)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'frequency)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'frequency)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'frequency)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'frequency)) ostream)
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'duty_cycle)) ostream)
  (cl:let ((bits (roslisp-utils:encode-single-float-bits (cl:slot-value msg 'duration))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) bits) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) bits) ostream))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <PWMOutputGoal>) istream)
  "Deserializes a message object of type '<PWMOutputGoal>"
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'pin_number)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'frequency)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 8) (cl:slot-value msg 'frequency)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 16) (cl:slot-value msg 'frequency)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 24) (cl:slot-value msg 'frequency)) (cl:read-byte istream))
    (cl:setf (cl:ldb (cl:byte 8 0) (cl:slot-value msg 'duty_cycle)) (cl:read-byte istream))
    (cl:let ((bits 0))
      (cl:setf (cl:ldb (cl:byte 8 0) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) bits) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) bits) (cl:read-byte istream))
    (cl:setf (cl:slot-value msg 'duration) (roslisp-utils:decode-single-float-bits bits)))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<PWMOutputGoal>)))
  "Returns string type for a message object of type '<PWMOutputGoal>"
  "my_action_pkg/PWMOutputGoal")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'PWMOutputGoal)))
  "Returns string type for a message object of type 'PWMOutputGoal"
  "my_action_pkg/PWMOutputGoal")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<PWMOutputGoal>)))
  "Returns md5sum for a message object of type '<PWMOutputGoal>"
  "1ff9352c3095a80174b88fcd113a603a")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'PWMOutputGoal)))
  "Returns md5sum for a message object of type 'PWMOutputGoal"
  "1ff9352c3095a80174b88fcd113a603a")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<PWMOutputGoal>)))
  "Returns full string definition for message of type '<PWMOutputGoal>"
  (cl:format cl:nil "# ====== DO NOT MODIFY! AUTOGENERATED FROM AN ACTION DEFINITION ======~%# goal definition~%uint8 pin_number           # GPIO 引脚号 (BCM 编号)~%uint32 frequency           # PWM 频率~%uint8 duty_cycle           # 占空比 0-100%~%float32 duration           # 持续时间 (秒)~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'PWMOutputGoal)))
  "Returns full string definition for message of type 'PWMOutputGoal"
  (cl:format cl:nil "# ====== DO NOT MODIFY! AUTOGENERATED FROM AN ACTION DEFINITION ======~%# goal definition~%uint8 pin_number           # GPIO 引脚号 (BCM 编号)~%uint32 frequency           # PWM 频率~%uint8 duty_cycle           # 占空比 0-100%~%float32 duration           # 持续时间 (秒)~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <PWMOutputGoal>))
  (cl:+ 0
     1
     4
     1
     4
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <PWMOutputGoal>))
  "Converts a ROS message object to a list"
  (cl:list 'PWMOutputGoal
    (cl:cons ':pin_number (pin_number msg))
    (cl:cons ':frequency (frequency msg))
    (cl:cons ':duty_cycle (duty_cycle msg))
    (cl:cons ':duration (duration msg))
))
