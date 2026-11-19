#!/bin/sh
# SMB 共有（Raspberry Pi の Samba / Windows の共有フォルダ）を Brick Pro にマウントする
# （rclone + FUSE。Chrome 用の chroot /opt/brick-chrome の中の rclone を使う）
# 置き場所: /opt/brick-chrome/smb-mount.sh   使い方: smb-mount.sh start | stop | restart | status
# 設定: /mnt/UDISK/smb-mount.conf（HOST / SMBUSER / SMBPASS(rclone obscure 済み) / BINDS）
R=/opt/brick-chrome
CONF=/mnt/UDISK/smb-mount.conf
TOP=/mnt/smb                     # サーバーの共有の一覧がここに並ぶ（純正の動画アプリは /mnt/ から開ける）
LOG=/tmp/smb-mount.log

[ -f "$CONF" ] || { echo "no $CONF"; exit 1; }
. "$CONF"

chroot_mounts() {
    for m in /proc /sys /dev /dev/pts; do
        mkdir -p $R$m
        grep -q " $R$m " /proc/mounts || mount -o bind $m $R$m
    done
    cp /etc/resolv.conf $R/etc/resolv.conf 2>/dev/null
}

unbind_all() {
    # BINDS の逆順に外す
    grep " fuse.rclone " /proc/mounts | awk '{print $2}' | grep -v "^$R" | sort -r | while read -r p; do
        umount "$p" 2>/dev/null || umount -l "$p"
    done
}

start() {
    grep -q " $TOP fuse.rclone " /proc/mounts && { echo "already mounted"; return 0; }
    # Wi-Fi が使えるまで最大 60 秒待つ
    i=0
    until ping -c 1 -W 1 "$HOST" >/dev/null 2>&1; do
        i=$((i + 1)); [ $i -ge 60 ] && { echo "$HOST unreachable" >> $LOG; return 1; }
        sleep 1
    done
    chroot_mounts
    mkdir -p $R/mnt/smb $TOP
    chroot $R /usr/local/bin/rclone mount ":smb,host=$HOST,user=$SMBUSER,pass=$SMBPASS:" /mnt/smb \
        --read-only --allow-other --daemon --dir-cache-time 1m --vfs-cache-mode off \
        --log-file /tmp/rclone.log --log-level NOTICE </dev/null >/dev/null 2>&1 || return 1
    for n in 1 2 3 4 5 6 7 8 9 10; do
        grep -q " $R/mnt/smb fuse.rclone " /proc/mounts && break; sleep 1
    done
    mount --bind $R/mnt/smb $TOP
    # BINDS: 「共有内のパス:Brick 側のフォルダ」を空白区切り
    for b in $BINDS; do
        src="$TOP/${b%%:*}"; dst="${b#*:}"
        [ -d "$src" ] || { echo "skip $src" >> $LOG; continue; }
        mkdir -p "$dst" && mount --bind "$src" "$dst"
    done
    echo "mounted $(date)" >> $LOG
}

stop() {
    unbind_all
    umount $R/mnt/smb 2>/dev/null || umount -l $R/mnt/smb
    for p in $(pgrep -f "rclone mount"); do kill $p; done
    # 空になったマウント先フォルダを消す（SD に空フォルダを残さない）
    for b in $BINDS; do rmdir "${b#*:}" 2>/dev/null; done
}

case "$1" in
    start) start ;;
    stop) stop ;;
    restart) stop; start ;;
    status) grep fuse.rclone /proc/mounts ;;
    *) echo "usage: $0 start|stop|restart|status"; exit 1 ;;
esac
