; Auto-generated. Do not edit!


(cl:in-package communication-srv)


;//! \htmlinclude NetworkCommunication-request.msg.html

(cl:defclass <NetworkCommunication-request> (roslisp-msg-protocol:ros-message)
  ((server_ip
    :reader server_ip
    :initarg :server_ip
    :type cl:string
    :initform "")
   (server_port
    :reader server_port
    :initarg :server_port
    :type cl:integer
    :initform 0)
   (message
    :reader message
    :initarg :message
    :type cl:string
    :initform ""))
)

(cl:defclass NetworkCommunication-request (<NetworkCommunication-request>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <NetworkCommunication-request>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'NetworkCommunication-request)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name communication-srv:<NetworkCommunication-request> is deprecated: use communication-srv:NetworkCommunication-request instead.")))

(cl:ensure-generic-function 'server_ip-val :lambda-list '(m))
(cl:defmethod server_ip-val ((m <NetworkCommunication-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader communication-srv:server_ip-val is deprecated.  Use communication-srv:server_ip instead.")
  (server_ip m))

(cl:ensure-generic-function 'server_port-val :lambda-list '(m))
(cl:defmethod server_port-val ((m <NetworkCommunication-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader communication-srv:server_port-val is deprecated.  Use communication-srv:server_port instead.")
  (server_port m))

(cl:ensure-generic-function 'message-val :lambda-list '(m))
(cl:defmethod message-val ((m <NetworkCommunication-request>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader communication-srv:message-val is deprecated.  Use communication-srv:message instead.")
  (message m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <NetworkCommunication-request>) ostream)
  "Serializes a message object of type '<NetworkCommunication-request>"
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'server_ip))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'server_ip))
  (cl:let* ((signed (cl:slot-value msg 'server_port)) (unsigned (cl:if (cl:< signed 0) (cl:+ signed 4294967296) signed)))
    (cl:write-byte (cl:ldb (cl:byte 8 0) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) unsigned) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) unsigned) ostream)
    )
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'message))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'message))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <NetworkCommunication-request>) istream)
  "Deserializes a message object of type '<NetworkCommunication-request>"
    (cl:let ((__ros_str_len 0))
      (cl:setf (cl:ldb (cl:byte 8 0) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) __ros_str_len) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'server_ip) (cl:make-string __ros_str_len))
      (cl:dotimes (__ros_str_idx __ros_str_len msg)
        (cl:setf (cl:char (cl:slot-value msg 'server_ip) __ros_str_idx) (cl:code-char (cl:read-byte istream)))))
    (cl:let ((unsigned 0))
      (cl:setf (cl:ldb (cl:byte 8 0) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 8) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 16) unsigned) (cl:read-byte istream))
      (cl:setf (cl:ldb (cl:byte 8 24) unsigned) (cl:read-byte istream))
      (cl:setf (cl:slot-value msg 'server_port) (cl:if (cl:< unsigned 2147483648) unsigned (cl:- unsigned 4294967296))))
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
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<NetworkCommunication-request>)))
  "Returns string type for a service object of type '<NetworkCommunication-request>"
  "communication/NetworkCommunicationRequest")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'NetworkCommunication-request)))
  "Returns string type for a service object of type 'NetworkCommunication-request"
  "communication/NetworkCommunicationRequest")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<NetworkCommunication-request>)))
  "Returns md5sum for a message object of type '<NetworkCommunication-request>"
  "1669b1e1911ecbb5ee2158c03f61fe58")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'NetworkCommunication-request)))
  "Returns md5sum for a message object of type 'NetworkCommunication-request"
  "1669b1e1911ecbb5ee2158c03f61fe58")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<NetworkCommunication-request>)))
  "Returns full string definition for message of type '<NetworkCommunication-request>"
  (cl:format cl:nil "string server_ip~%int32 server_port~%string message~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'NetworkCommunication-request)))
  "Returns full string definition for message of type 'NetworkCommunication-request"
  (cl:format cl:nil "string server_ip~%int32 server_port~%string message~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <NetworkCommunication-request>))
  (cl:+ 0
     4 (cl:length (cl:slot-value msg 'server_ip))
     4
     4 (cl:length (cl:slot-value msg 'message))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <NetworkCommunication-request>))
  "Converts a ROS message object to a list"
  (cl:list 'NetworkCommunication-request
    (cl:cons ':server_ip (server_ip msg))
    (cl:cons ':server_port (server_port msg))
    (cl:cons ':message (message msg))
))
;//! \htmlinclude NetworkCommunication-response.msg.html

(cl:defclass <NetworkCommunication-response> (roslisp-msg-protocol:ros-message)
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

(cl:defclass NetworkCommunication-response (<NetworkCommunication-response>)
  ())

(cl:defmethod cl:initialize-instance :after ((m <NetworkCommunication-response>) cl:&rest args)
  (cl:declare (cl:ignorable args))
  (cl:unless (cl:typep m 'NetworkCommunication-response)
    (roslisp-msg-protocol:msg-deprecation-warning "using old message class name communication-srv:<NetworkCommunication-response> is deprecated: use communication-srv:NetworkCommunication-response instead.")))

(cl:ensure-generic-function 'success-val :lambda-list '(m))
(cl:defmethod success-val ((m <NetworkCommunication-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader communication-srv:success-val is deprecated.  Use communication-srv:success instead.")
  (success m))

(cl:ensure-generic-function 'response-val :lambda-list '(m))
(cl:defmethod response-val ((m <NetworkCommunication-response>))
  (roslisp-msg-protocol:msg-deprecation-warning "Using old-style slot reader communication-srv:response-val is deprecated.  Use communication-srv:response instead.")
  (response m))
(cl:defmethod roslisp-msg-protocol:serialize ((msg <NetworkCommunication-response>) ostream)
  "Serializes a message object of type '<NetworkCommunication-response>"
  (cl:write-byte (cl:ldb (cl:byte 8 0) (cl:if (cl:slot-value msg 'success) 1 0)) ostream)
  (cl:let ((__ros_str_len (cl:length (cl:slot-value msg 'response))))
    (cl:write-byte (cl:ldb (cl:byte 8 0) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 8) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 16) __ros_str_len) ostream)
    (cl:write-byte (cl:ldb (cl:byte 8 24) __ros_str_len) ostream))
  (cl:map cl:nil #'(cl:lambda (c) (cl:write-byte (cl:char-code c) ostream)) (cl:slot-value msg 'response))
)
(cl:defmethod roslisp-msg-protocol:deserialize ((msg <NetworkCommunication-response>) istream)
  "Deserializes a message object of type '<NetworkCommunication-response>"
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
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql '<NetworkCommunication-response>)))
  "Returns string type for a service object of type '<NetworkCommunication-response>"
  "communication/NetworkCommunicationResponse")
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'NetworkCommunication-response)))
  "Returns string type for a service object of type 'NetworkCommunication-response"
  "communication/NetworkCommunicationResponse")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql '<NetworkCommunication-response>)))
  "Returns md5sum for a message object of type '<NetworkCommunication-response>"
  "1669b1e1911ecbb5ee2158c03f61fe58")
(cl:defmethod roslisp-msg-protocol:md5sum ((type (cl:eql 'NetworkCommunication-response)))
  "Returns md5sum for a message object of type 'NetworkCommunication-response"
  "1669b1e1911ecbb5ee2158c03f61fe58")
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql '<NetworkCommunication-response>)))
  "Returns full string definition for message of type '<NetworkCommunication-response>"
  (cl:format cl:nil "bool success~%string response~%~%~%"))
(cl:defmethod roslisp-msg-protocol:message-definition ((type (cl:eql 'NetworkCommunication-response)))
  "Returns full string definition for message of type 'NetworkCommunication-response"
  (cl:format cl:nil "bool success~%string response~%~%~%"))
(cl:defmethod roslisp-msg-protocol:serialization-length ((msg <NetworkCommunication-response>))
  (cl:+ 0
     1
     4 (cl:length (cl:slot-value msg 'response))
))
(cl:defmethod roslisp-msg-protocol:ros-message-to-list ((msg <NetworkCommunication-response>))
  "Converts a ROS message object to a list"
  (cl:list 'NetworkCommunication-response
    (cl:cons ':success (success msg))
    (cl:cons ':response (response msg))
))
(cl:defmethod roslisp-msg-protocol:service-request-type ((msg (cl:eql 'NetworkCommunication)))
  'NetworkCommunication-request)
(cl:defmethod roslisp-msg-protocol:service-response-type ((msg (cl:eql 'NetworkCommunication)))
  'NetworkCommunication-response)
(cl:defmethod roslisp-msg-protocol:ros-datatype ((msg (cl:eql 'NetworkCommunication)))
  "Returns string type for a service object of type '<NetworkCommunication>"
  "communication/NetworkCommunication")