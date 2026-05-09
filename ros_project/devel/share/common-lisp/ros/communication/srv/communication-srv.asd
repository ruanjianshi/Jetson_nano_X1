
(cl:in-package :asdf)

(defsystem "communication-srv"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "NetworkCommunication" :depends-on ("_package_NetworkCommunication"))
    (:file "_package_NetworkCommunication" :depends-on ("_package"))
    (:file "SerialCommunication" :depends-on ("_package_SerialCommunication"))
    (:file "_package_SerialCommunication" :depends-on ("_package"))
  ))