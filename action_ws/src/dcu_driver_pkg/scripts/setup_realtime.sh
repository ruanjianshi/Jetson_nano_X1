# 添加实时调度权限
# 将以下内容添加到 /etc/security/limits.conf

# jetson user real-time scheduling
jetson    -    rtprio    99
jetson    -    nice      -20
jetson    -    memlock    unlimited

# 或者一行：
# jetson - rtprio 99 && jetson - nice -20 && jetson - memlock unlimited
