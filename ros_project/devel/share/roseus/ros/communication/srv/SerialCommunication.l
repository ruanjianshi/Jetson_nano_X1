;; Auto-generated. Do not edit!


(when (boundp 'communication::SerialCommunication)
  (if (not (find-package "COMMUNICATION"))
    (make-package "COMMUNICATION"))
  (shadow 'SerialCommunication (find-package "COMMUNICATION")))
(unless (find-package "COMMUNICATION::SERIALCOMMUNICATION")
  (make-package "COMMUNICATION::SERIALCOMMUNICATION"))
(unless (find-package "COMMUNICATION::SERIALCOMMUNICATIONREQUEST")
  (make-package "COMMUNICATION::SERIALCOMMUNICATIONREQUEST"))
(unless (find-package "COMMUNICATION::SERIALCOMMUNICATIONRESPONSE")
  (make-package "COMMUNICATION::SERIALCOMMUNICATIONRESPONSE"))

(in-package "ROS")





(defclass communication::SerialCommunicationRequest
  :super ros::object
  :slots (_port _baud_rate _data ))

(defmethod communication::SerialCommunicationRequest
  (:init
   (&key
    ((:port __port) "")
    ((:baud_rate __baud_rate) 0)
    ((:data __data) "")
    )
   (send-super :init)
   (setq _port (string __port))
   (setq _baud_rate (round __baud_rate))
   (setq _data (string __data))
   self)
  (:port
   (&optional __port)
   (if __port (setq _port __port)) _port)
  (:baud_rate
   (&optional __baud_rate)
   (if __baud_rate (setq _baud_rate __baud_rate)) _baud_rate)
  (:data
   (&optional __data)
   (if __data (setq _data __data)) _data)
  (:serialization-length
   ()
   (+
    ;; string _port
    4 (length _port)
    ;; int32 _baud_rate
    4
    ;; string _data
    4 (length _data)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; string _port
       (write-long (length _port) s) (princ _port s)
     ;; int32 _baud_rate
       (write-long _baud_rate s)
     ;; string _data
       (write-long (length _data) s) (princ _data s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; string _port
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _port (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;; int32 _baud_rate
     (setq _baud_rate (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; string _data
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _data (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(defclass communication::SerialCommunicationResponse
  :super ros::object
  :slots (_success _response ))

(defmethod communication::SerialCommunicationResponse
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

(defclass communication::SerialCommunication
  :super ros::object
  :slots ())

(setf (get communication::SerialCommunication :md5sum-) "463ba1f6ee8cee968834e03f974654f4")
(setf (get communication::SerialCommunication :datatype-) "communication/SerialCommunication")
(setf (get communication::SerialCommunication :request) communication::SerialCommunicationRequest)
(setf (get communication::SerialCommunication :response) communication::SerialCommunicationResponse)

(defmethod communication::SerialCommunicationRequest
  (:response () (instance communication::SerialCommunicationResponse :init)))

(setf (get communication::SerialCommunicationRequest :md5sum-) "463ba1f6ee8cee968834e03f974654f4")
(setf (get communication::SerialCommunicationRequest :datatype-) "communication/SerialCommunicationRequest")
(setf (get communication::SerialCommunicationRequest :definition-)
      "string port
int32 baud_rate
string data
---
bool success
string response
")

(setf (get communication::SerialCommunicationResponse :md5sum-) "463ba1f6ee8cee968834e03f974654f4")
(setf (get communication::SerialCommunicationResponse :datatype-) "communication/SerialCommunicationResponse")
(setf (get communication::SerialCommunicationResponse :definition-)
      "string port
int32 baud_rate
string data
---
bool success
string response
")



(provide :communication/SerialCommunication "463ba1f6ee8cee968834e03f974654f4")


