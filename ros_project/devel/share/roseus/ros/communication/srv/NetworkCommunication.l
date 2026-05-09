;; Auto-generated. Do not edit!


(when (boundp 'communication::NetworkCommunication)
  (if (not (find-package "COMMUNICATION"))
    (make-package "COMMUNICATION"))
  (shadow 'NetworkCommunication (find-package "COMMUNICATION")))
(unless (find-package "COMMUNICATION::NETWORKCOMMUNICATION")
  (make-package "COMMUNICATION::NETWORKCOMMUNICATION"))
(unless (find-package "COMMUNICATION::NETWORKCOMMUNICATIONREQUEST")
  (make-package "COMMUNICATION::NETWORKCOMMUNICATIONREQUEST"))
(unless (find-package "COMMUNICATION::NETWORKCOMMUNICATIONRESPONSE")
  (make-package "COMMUNICATION::NETWORKCOMMUNICATIONRESPONSE"))

(in-package "ROS")





(defclass communication::NetworkCommunicationRequest
  :super ros::object
  :slots (_server_ip _server_port _message ))

(defmethod communication::NetworkCommunicationRequest
  (:init
   (&key
    ((:server_ip __server_ip) "")
    ((:server_port __server_port) 0)
    ((:message __message) "")
    )
   (send-super :init)
   (setq _server_ip (string __server_ip))
   (setq _server_port (round __server_port))
   (setq _message (string __message))
   self)
  (:server_ip
   (&optional __server_ip)
   (if __server_ip (setq _server_ip __server_ip)) _server_ip)
  (:server_port
   (&optional __server_port)
   (if __server_port (setq _server_port __server_port)) _server_port)
  (:message
   (&optional __message)
   (if __message (setq _message __message)) _message)
  (:serialization-length
   ()
   (+
    ;; string _server_ip
    4 (length _server_ip)
    ;; int32 _server_port
    4
    ;; string _message
    4 (length _message)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _server_ip
       (write-long (length _server_ip) s) (princ _server_ip s)
     ;; int32 _server_port
       (write-long _server_port s)
     ;; string _message
       (write-long (length _message) s) (princ _message s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _server_ip
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _server_ip (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; int32 _server_port
     (setq _server_port (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; string _message
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _message (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(defclass communication::NetworkCommunicationResponse
  :super ros::object
  :slots (_success _response ))

(defmethod communication::NetworkCommunicationResponse
  (:init
   (&key
    ((:success __success) nil)
    ((:response __response) "")
    )
   (send-super :init)
   (setq _success __success)
   (setq _response (string __response))
   self)
  (:success
   (&optional (__success :null))
   (if (not (eq __success :null)) (setq _success __success)) _success)
  (:response
   (&optional __response)
   (if __response (setq _response __response)) _response)
  (:serialization-length
   ()
   (+
    ;; bool _success
    1
    ;; string _response
    4 (length _response)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; bool _success
       (if _success (write-byte -1 s) (write-byte 0 s))
     ;; string _response
       (write-long (length _response) s) (princ _response s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; bool _success
     (setq _success (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; string _response
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _response (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(defclass communication::NetworkCommunication
  :super ros::object
  :slots ())

(setf (get communication::NetworkCommunication :md5sum-) "1669b1e1911ecbb5ee2158c03f61fe58")
(setf (get communication::NetworkCommunication :datatype-) "communication/NetworkCommunication")
(setf (get communication::NetworkCommunication :request) communication::NetworkCommunicationRequest)
(setf (get communication::NetworkCommunication :response) communication::NetworkCommunicationResponse)

(defmethod communication::NetworkCommunicationRequest
  (:response () (instance communication::NetworkCommunicationResponse :init)))

(setf (get communication::NetworkCommunicationRequest :md5sum-) "1669b1e1911ecbb5ee2158c03f61fe58")
(setf (get communication::NetworkCommunicationRequest :datatype-) "communication/NetworkCommunicationRequest")
(setf (get communication::NetworkCommunicationRequest :definition-)
      "string server_ip
int32 server_port
string message
---
bool success
string response
")

(setf (get communication::NetworkCommunicationResponse :md5sum-) "1669b1e1911ecbb5ee2158c03f61fe58")
(setf (get communication::NetworkCommunicationResponse :datatype-) "communication/NetworkCommunicationResponse")
(setf (get communication::NetworkCommunicationResponse :definition-)
      "string server_ip
int32 server_port
string message
---
bool success
string response
")



(provide :communication/NetworkCommunication "1669b1e1911ecbb5ee2158c03f61fe58")


