; Auto-generated. Do not edit!


(cl:in-package gpio_control-srv)


;//! \htmlinclude GPIOControl-request.msg.html

(cl:defclass <GPIOControl-request> (roslisp-msg-protocol:ros-message)
  ((pin_number
    :reader pin_number
    :initarg :pin_number
    :type cl:integer
    :initform 0)
   (state
    :reader state
    :initarg :state
    :type cl:boolean
    :initform cl:nil))
)

(cl:defclass GPIOControl-request (<GPIOControl-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <GPIOControl-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'GPIOControl-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name gpio_control-srv:<GPIOControl-request> is deprecated: use gpio_control-srv:GPIOControl-request instead.")))

(cl:ensure-generic-function 'pin_number-val :lambda-list '(m))
(cl:defmethod pin_number-val ((m <GPIOControl-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader gpio_control-srv:pin_number-val is deprecated.  Use gpio_control-srv:pin_number instead.")
  (pin_number m))

(cl:ensure-generic-function 'state-val :lambda-list '(m))
(cl:defmethod state-val ((m <GPIOControl-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader gpio_control-srv:state-val is deprecated.  Use gpio_control-srv:state instead.")
  (state m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <GPIOControl-request>) ostream)
  "Serializes a message object of type '<GPIOControl-request>"
  (cl:let* ((signed (cl:slot-value msg 'pin_number)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'state) 1 0)) ostream)
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <GPIOControl-request>) istream)
  "Deserializes a message object of type '<GPIOControl-request>"
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'pin_number) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:setf (cl:slot-value msg 'state) (cl:not (cl:zerop (cl:read-byte istream))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<GPIOControl-request>)))
  "Returns string type for a service object of type '<GPIOControl-request>"
  "gpio_control/GPIOControlRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'GPIOControl-request)))
  "Returns string type for a service object of type 'GPIOControl-request"
  "gpio_control/GPIOControlRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<GPIOControl-request>)))
  "Returns md5sum for a message object of type '<GPIOControl-request>"
  "fb7e1816990c224213820b65098f630b")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'GPIOControl-request)))
  "Returns md5sum for a message object of type 'GPIOControl-request"
  "fb7e1816990c224213820b65098f630b")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<GPIOControl-request>)))
  "Returns full string definition for message of type '<GPIOControl-request>"
  (cl:format cl:nil "int32 pin_number~%bool state~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'GPIOControl-request)))
  "Returns full string definition for message of type 'GPIOControl-request"
  (cl:format cl:nil "int32 pin_number~%bool state~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <GPIOControl-request>))
  (cl:+ 0
     4
     1
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <GPIOControl-request>))
  "Converts a ROS message object to a list"
  (cl:list 'GPIOControl-request
    (cl:cons ':pin_number (pin_number msg))
    (cl:cons ':state (state msg))
))
;//! \htmlinclude GPIOControl-response.msg.html

(cl:defclass <GPIOControl-response> (roslisp-msg-protocol:ros-message)
  ((success
    :reader success
    :initarg :success
    :type cl:boolean
    :initform cl:nil)
   (message
    :reader message
    :initarg :message
    :type cl:string
    :initform ""))
)

(cl:defclass GPIOControl-response (<GPIOControl-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <GPIOControl-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'GPIOControl-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name gpio_control-srv:<GPIOControl-response> is deprecated: use gpio_control-srv:GPIOControl-response instead.")))

(cl:ensure-generic-function 'success-val :lambda-list '(m))
(cl:defmethod success-val ((m <GPIOControl-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader gpio_control-srv:success-val is deprecated.  Use gpio_control-srv:success instead.")
  (success m))

(cl:ensure-generic-function 'message-val :lambda-list '(m))
(cl:defmethod message-val ((m <GPIOControl-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader gpio_control-srv:message-val is deprecated.  Use gpio_control-srv:message instead.")
  (message m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <GPIOControl-response>) ostream)
  "Serializes a message object of type '<GPIOControl-response>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'success) 1 0)) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'message))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'message))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <GPIOControl-response>) istream)
  "Deserializes a message object of type '<GPIOControl-response>"
    (cl:setf (cl:slot-value msg 'success) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'message) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'message) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<GPIOControl-response>)))
  "Returns string type for a service object of type '<GPIOControl-response>"
  "gpio_control/GPIOControlResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'GPIOControl-response)))
  "Returns string type for a service object of type 'GPIOControl-response"
  "gpio_control/GPIOControlResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<GPIOControl-response>)))
  "Returns md5sum for a message object of type '<GPIOControl-response>"
  "fb7e1816990c224213820b65098f630b")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'GPIOControl-response)))
  "Returns md5sum for a message object of type 'GPIOControl-response"
  "fb7e1816990c224213820b65098f630b")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<GPIOControl-response>)))
  "Returns full string definition for message of type '<GPIOControl-response>"
  (cl:format cl:nil "bool success~%string message~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'GPIOControl-response)))
  "Returns full string definition for message of type 'GPIOControl-response"
  (cl:format cl:nil "bool success~%string message~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <GPIOControl-response>))
  (cl:+ 0
     1
     4 (cl:length (cl:slot-value msg 'message))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <GPIOControl-response>))
  "Converts a ROS message object to a list"
  (cl:list 'GPIOControl-response
    (cl:cons ':success (success msg))
    (cl:cons ':message (message msg))
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'GPIOControl)))
  'GPIOControl-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'GPIOControl)))
  'GPIOControl-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'GPIOControl)))
  "Returns string type for a service object of type '<GPIOControl>"
  "gpio_control/GPIOControl")