;; Auto-generated. Do not edit!


(when (boundp 'gpio_control::GPIOControl)
  (if (not (find-package "GPIO_CONTROL"))
    (make-package "GPIO_CONTROL"))
  (shadow 'GPIOControl (find-package "GPIO_CONTROL")))
(unless (find-package "GPIO_CONTROL::GPIOCONTROL")
  (make-package "GPIO_CONTROL::GPIOCONTROL"))
(unless (find-package "GPIO_CONTROL::GPIOCONTROLREQUEST")
  (make-package "GPIO_CONTROL::GPIOCONTROLREQUEST"))
(unless (find-package "GPIO_CONTROL::GPIOCONTROLRESPONSE")
  (make-package "GPIO_CONTROL::GPIOCONTROLRESPONSE"))

(in-package "ROS")





(defclass gpio_control::GPIOControlRequest
  :super ros::object
  :slots (_pin_number _state ))

(defmethod gpio_control::GPIOControlRequest
  (:init
   (&key
    ((:pin_number __pin_number) 0)
    ((:state __state) nil)
    )
   (send-super :init)
   (setq _pin_number (round __pin_number))
   (setq _state __state)
   self)
  (:pin_number
   (&optional __pin_number)
   (if __pin_number (setq _pin_number __pin_number)) _pin_number)
  (:state
   (&optional (__state :null))
   (if (not (eq __state :null)) (setq _state __state)) _state)
  (:serialization-length
   ()
   (+
    ;; int32 _pin_number
    4
    ;; bool _state
    1
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; int32 _pin_number
       (write-long _pin_number s)
     ;; bool _state
       (if _state (write-byte -1 s) (write-byte 0 s))
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; int32 _pin_number
     (setq _pin_number (sys::peek buf ptr- :integer)) (incf ptr- 4)
   ;; bool _state
     (setq _state (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;;
   self)
  )

(defclass gpio_control::GPIOControlResponse
  :super ros::object
  :slots (_success _message ))

(defmethod gpio_control::GPIOControlResponse
  (:init
   (&key
    ((:success __success) nil)
    ((:message __message) "")
    )
   (send-super :init)
   (setq _success __success)
   (setq _message (string __message))
   self)
  (:success
   (&optional (__success :null))
   (if (not (eq __success :null)) (setq _success __success)) _success)
  (:message
   (&optional __message)
   (if __message (setq _message __message)) _message)
  (:serialization-length
   ()
   (+
    ;; bool _success
    1
    ;; string _message
    4 (length _message)
    ))
  (:serialize
   (&optional strm)
   (let ((s (if strm strm
              (make-string-output-stream (send self :serialization-length)))))
     ;; bool _success
       (if _success (write-byte -1 s) (write-byte 0 s))
     ;; string _message
       (write-long (length _message) s) (princ _message s)
     ;;
     (if (null strm) (get-output-stream-string s))))
  (:deserialize
   (buf &optional (ptr- 0))
   ;; bool _success
     (setq _success (not (= 0 (sys::peek buf ptr- :char)))) (incf ptr- 1)
   ;; string _message
     (let (n) (setq n (sys::peek buf ptr- :integer)) (incf ptr- 4) (setq _message (subseq buf ptr- (+ ptr- n))) (incf ptr- n))
   ;;
   self)
  )

(defclass gpio_control::GPIOControl
  :super ros::object
  :slots ())

(setf (get gpio_control::GPIOControl :md5sum-) "fb7e1816990c224213820b65098f630b")
(setf (get gpio_control::GPIOControl :datatype-) "gpio_control/GPIOControl")
(setf (get gpio_control::GPIOControl :request) gpio_control::GPIOControlRequest)
(setf (get gpio_control::GPIOControl :response) gpio_control::GPIOControlResponse)

(defmethod gpio_control::GPIOControlRequest
  (:response () (instance gpio_control::GPIOControlResponse :init)))

(setf (get gpio_control::GPIOControlRequest :md5sum-) "fb7e1816990c224213820b65098f630b")
(setf (get gpio_control::GPIOControlRequest :datatype-) "gpio_control/GPIOControlRequest")
(setf (get gpio_control::GPIOControlRequest :definition-)
      "int32 pin_number
bool state
---
bool success
string message
")

(setf (get gpio_control::GPIOControlResponse :md5sum-) "fb7e1816990c224213820b65098f630b")
(setf (get gpio_control::GPIOControlResponse :datatype-) "gpio_control/GPIOControlResponse")
(setf (get gpio_control::GPIOControlResponse :definition-)
      "int32 pin_number
bool state
---
bool success
string message
")



(provide :gpio_control/GPIOControl "fb7e1816990c224213820b65098f630b")


