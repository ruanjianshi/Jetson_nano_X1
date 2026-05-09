
(cl:in-package :asdf)

(defsystem "gpio_control-srv"
  :depends-on (:roslisp-msg-protocol :roslisp-utils )
  :components ((:file "_package")
    (:file "GPIOControl" :depends-on ("_package_GPIOControl"))
    (:file "_package_GPIOControl" :depends-on ("_package"))
  ))