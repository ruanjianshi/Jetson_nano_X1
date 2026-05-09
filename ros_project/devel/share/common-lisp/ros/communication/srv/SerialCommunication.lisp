; Auto-generated. Do not edit!


(cl:in-package communication-srv)


;//! \htmlinclude SerialCommunication-request.msg.html

(cl:defclass <SerialCommunication-request> (roslisp-msg-protocol:ros-message)
  ((port
    :reader port
    :initarg :port
    :type cl:string
    :initform "")
   (baud_rate
    :reader baud_rate
    :initarg :baud_rate
    :type cl:integer
    :initform 0)
   (data
    :reader data
    :initarg :data
    :type cl:string
    :initform ""))
)

(cl:defclass SerialCommunication-request (<SerialCommunication-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <SerialCommunication-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'SerialCommunication-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name communication-srv:<SerialCommunication-request> is deprecated: use communication-srv:SerialCommunication-request instead.")))

(cl:ensure-generic-function 'port-val :lambda-list '(m))
(cl:defmethod port-val ((m <SerialCommunication-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader communication-srv:port-val is deprecated.  Use communication-srv:port instead.")
  (port m))

(cl:ensure-generic-function 'baud_rate-val :lambda-list '(m))
(cl:defmethod baud_rate-val ((m <SerialCommunication-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader communication-srv:baud_rate-val is deprecated.  Use communication-srv:baud_rate instead.")
  (baud_rate m))

(cl:ensure-generic-function 'data-val :lambda-list '(m))
(cl:defmethod data-val ((m <SerialCommunication-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader communication-srv:data-val is deprecated.  Use communication-srv:data instead.")
  (data m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <SerialCommunication-request>) ostream)
  "Serializes a message object of type '<SerialCommunication-request>"
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'port))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'port))
  (cl:let* ((signed (cl:slot-value msg 'baud_rate)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'data))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'data))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <SerialCommunication-request>) istream)
  "Deserializes a message object of type '<SerialCommunication-request>"
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'port) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'port) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'baud_rate) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'data) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'data) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<SerialCommunication-request>)))
  "Returns string type for a service object of type '<SerialCommunication-request>"
  "communication/SerialCommunicationRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'SerialCommunication-request)))
  "Returns string type for a service object of type 'SerialCommunication-request"
  "communication/SerialCommunicationRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<SerialCommunication-request>)))
  "Returns md5sum for a message object of type '<SerialCommunication-request>"
  "463ba1f6ee8cee968834e03f974654f4")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'SerialCommunication-request)))
  "Returns md5sum for a message object of type 'SerialCommunication-request"
  "463ba1f6ee8cee968834e03f974654f4")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<SerialCommunication-request>)))
  "Returns full string definition for message of type '<SerialCommunication-request>"
  (cl:format cl:nil "string port~%int32 baud_rate~%string data~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'SerialCommunication-request)))
  "Returns full string definition for message of type 'SerialCommunication-request"
  (cl:format cl:nil "string port~%int32 baud_rate~%string data~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <SerialCommunication-request>))
  (cl:+ 0
     4 (cl:length (cl:slot-value msg 'port))
     4
     4 (cl:length (cl:slot-value msg 'data))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <SerialCommunication-request>))
  "Converts a ROS message object to a list"
  (cl:list 'SerialCommunication-request
    (cl:cons ':port (port msg))
    (cl:cons ':baud_rate (baud_rate msg))
    (cl:cons ':data (data msg))
))
;//! \htmlinclude SerialCommunication-response.msg.html

(cl:defclass <SerialCommunication-response> (roslisp-msg-protocol:ros-message)
  ((success
    :reader success
    :initarg :success
    :type cl:boolean
    :initform cl:nil)
   (response
    :reader response
    :initarg :response
    :type cl:string
    :initform ""))
)

(cl:defclass SerialCommunication-response (<SerialCommunication-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <SerialCommunication-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'SerialCommunication-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name communication-srv:<SerialCommunication-response> is deprecated: use communication-srv:SerialCommunication-response instead.")))

(cl:ensure-generic-function 'success-val :lambda-list '(m))
(cl:defmethod success-val ((m <SerialCommunication-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader communication-srv:success-val is deprecated.  Use communication-srv:success instead.")
  (success m))

(cl:ensure-generic-function 'response-val :lambda-list '(m))
(cl:defmethod response-val ((m <SerialCommunication-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader communication-srv:response-val is deprecated.  Use communication-srv:response instead.")
  (response m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <SerialCommunication-response>) ostream)
  "Serializes a message object of type '<SerialCommunication-response>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'success) 1 0)) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'response))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'response))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <SerialCommunication-response>) istream)
  "Deserializes a message object of type '<SerialCommunication-response>"
    (cl:setf (cl:slot-value msg 'success) (cl:not (cl:zerop (cl:read-byte istream))))
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'response) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'response) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
  msg
)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<SerialCommunication-response>)))
  "Returns string type for a service object of type '<SerialCommunication-response>"
  "communication/SerialCommunicationResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'SerialCommunication-response)))
  "Returns string type for a service object of type 'SerialCommunication-response"
  "communication/SerialCommunicationResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<SerialCommunication-response>)))
  "Returns md5sum for a message object of type '<SerialCommunication-response>"
  "463ba1f6ee8cee968834e03f974654f4")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'SerialCommunication-response)))
  "Returns md5sum for a message object of type 'SerialCommunication-response"
  "463ba1f6ee8cee968834e03f974654f4")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<SerialCommunication-response>)))
  "Returns full string definition for message of type '<SerialCommunication-response>"
  (cl:format cl:nil "bool success~%string response~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'SerialCommunication-response)))
  "Returns full string definition for message of type 'SerialCommunication-response"
  (cl:format cl:nil "bool success~%string response~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <SerialCommunication-response>))
  (cl:+ 0
     1
     4 (cl:length (cl:slot-value msg 'response))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <SerialCommunication-response>))
  "Converts a ROS message object to a list"
  (cl:list 'SerialCommunication-response
    (cl:cons ':success (success msg))
    (cl:cons ':response (response msg))
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'SerialCommunication)))
  'SerialCommunication-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'SerialCommunication)))
  'SerialCommunication-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'SerialCommunication)))
  "Returns string type for a service object of type '<SerialCommunication>"
  "communication/SerialCommunication")