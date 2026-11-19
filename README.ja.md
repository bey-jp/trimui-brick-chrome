# brick-chrome 日本語版（TRIMUI Brick Pro で Google Chrome）

[vhu231/trimui-brick-chrome](https://github.com/vhu231/trimui-brick-chrome) のフォークです。
TRIMUI Brick Pro（TG4040）の純正ファームのまま、本物の Google Chrome を動かします。
仕組みや性能の詳細は元の [README.md](README.md)（中国語）を見てください。

このフォークで変えたこと:

- **日本語化**: Chrome の画面を日本語に（`--lang=ja`）、音声入力を日本語に（`BRICK_SPEECH_LANG=ja-JP`）、
  画面キーボードのキー名・状態表示・CONTROLS.txt を日本語に、日本語フォント（`fonts-noto-cjk`）を追加
- **日本語入力**: 画面キーボードでローマ字かな漢字変換（`brick_ime.py`、新規）
- **スワップの不具合修正**: `swap-udisk.sh` が内部ストレージのマウント前に動くとシステム領域があふれる問題
- **おまけ**: SMB 共有（Raspberry Pi の Samba など）のマウント（`extras/smb/`）、起動スクリプト（`extras/brickboot/`）

紹介記事: bey.jp（ブログ）

---

## 準備

- Brick Pro を Wi-Fi につなぎ、**設定 → デベロッパー** で SSH をオンにする
- Brick Pro の IP アドレスを調べる（ルーターの管理画面など）
- root のパスワードは Tina Linux の初期値（`tina`）。**導入が終わったら変更を推奨**（`passwd`）
- 作業する PC: Linux / Mac / Windows の WSL（Ubuntu）。Raspberry Pi でもよい
- PC に `ssh` `scp` `expect` `curl` `git` を入れる（Ubuntu なら `sudo apt install expect curl git`）
- 本体のシステム領域に 1.5GB 以上の空き（Brick Pro は約 1.9GB 空いている）。SD カードは挿したまま
- 所要時間は約 30〜40 分（大半は Brick Pro がパッケージをダウンロードする時間）

## 導入

PC で順に実行します。元の README の手順 0〜10 と同じで、日本語化は済んでいるので書き換えは不要です。

### 0. 取得と接続の設定

```bash
git clone https://github.com/bey-jp/trimui-brick-chrome
cd trimui-brick-chrome
export BRICK_HOST=192.168.x.x        # Brick Pro の IP
export BRICK_PASS='tina'             # root のパスワード
export BRICK_KNOWN_HOSTS=~/.brick_known_hosts
ssh-keyscan -T 5 -t ed25519 "$BRICK_HOST" > "$BRICK_KNOWN_HOSTS"
echo 'echo hello from $(uname -m)' | tools/brick-run -   # hello from aarch64 と出れば OK
```

### 1. Ubuntu と Chrome をダウンロード

```bash
curl -fL -O https://cdimage.ubuntu.com/ubuntu-base/releases/jammy/release/ubuntu-base-22.04.5-base-arm64.tar.gz
curl -fL -O https://cdimage.ubuntu.com/ubuntu-base/releases/jammy/release/SHA256SUMS
grep 22.04.5-base-arm64 SHA256SUMS; sha256sum ubuntu-base-22.04.5-base-arm64.tar.gz   # 一致を確認
curl -fL -o google-chrome-stable_current_arm64.deb \
  https://dl.google.com/linux/direct/google-chrome-stable_current_arm64.deb
```

### 2〜10. 元の README の手順どおり

[README.md の「完整安装教程」](README.md#完整安装教程) の手順 2〜10 のコマンドを、そのまま順に貼り付けます。

| 手順 | 内容 |
|---|---|
| 2 | Ubuntu を Brick Pro に送って `/opt/brick-chrome` に展開 |
| 3 | マウント・DNS・apt の設定（`apt-get update` まで） |
| 4 | 画面表示（X11）・Python・フォント・音声（このフォークでは `fonts-noto-cjk` 入り） |
| 5 | `xorg.conf` を送る |
| 6 | Chrome を入れる |
| 7 | 実行用のユーザー `brick` を作る（`inet` と `audio` のグループが必須） |
| 8 | 起動スクリプト類を送る（日本語版の `brick_keyboard.py` と新規の `brick_ime.py` が送られる） |
| 9 | GPU 加速（任意だが入れたほうが速い） |
| 10 | アプリ一覧に追加（MainUI が再起動して「Chrome」が出る） |

表示倍率は `/mnt/SDCARD/Apps/Chrome/scale.txt` に `1.5` と書くのがおすすめです（初期値 `1` は文字が小さい）。

### スワップ（推奨）

メモリが約 1GB でスワップがないため、本体内部に 1GB のスワップを作ります（初回は約 1 分）。

```bash
tools/brick-scp.exp sdcard/System/starts/swap-udisk.sh /tmp/swap-udisk.sh
echo 'sh /tmp/swap-udisk.sh; free -m' | tools/brick-run -
```

起動のたびに有効にするには、下の [brickboot](#起動スクリプト-brickboot) を入れます。
元の README のように SD カードの `System/starts/` に置く方法は、起動時に内部ストレージのマウントより先に動くことがあり、
システム領域に 700MB のファイルができて満杯になりました（このフォークの `swap-udisk.sh` は修正済み）。
また、純正の起動処理は SD カードのマウントを 3 秒しか待たないので、`System/starts/` 自体が動かないこともあります。

## 使い方

| ボタン | 動作 |
|---|---|
| 左スティック | ポインタを動かす |
| A / Y | クリック / 右クリック |
| B / X | Esc / 1文字消す |
| START / SELECT | Enter / Tab |
| 十字キー 上下 / 左右 | スクロール / 戻る・進む |
| L1 / R1 | ページアップ / ページダウン |
| L2 / R2 | 縮小 / 拡大 |
| 右スティック押し込み / 左スティック押し込み | アドレスバーへ / 再読み込み |
| MENU 短押し | 画面キーボード |
| MENU 長押し | 音声入力（https のページのみ） |
| SELECT + START | 終了 |

### 日本語入力

画面キーボード左下の「ABC」を押すと「あ」（紫）になり、日本語モードになります。

| 操作 | 動作 |
|---|---|
| ローマ字で打つ | 画面上部にひらがなで表示（`konnichiha` → こんにちは、`nn` → ん、`kitte` → きって） |
| スペース | 漢字に変換。続けて押すと次の候補（漢字 → カタカナ → ひらがな） |
| 改行 / START | 確定 |
| 削除 / X | 1文字消す（変換中は変換前に戻る） |
| B | 取り消し |
| `-` `.` `,` `/` | ー 。 、 ・ |

- 漢字の変換は Google の変換サービス（`https://www.google.com/transliterate`）を使います。ネット接続が必要で、変換する文字は Google に送られます。
- 本体に IME（fcitx・mozc）や辞書を入れないので、メモリが少ない Brick Pro でも軽く動きます。
- 文節の区切りは直せません。単語ごとに変換すると思いどおりになりやすいです。

## おまけ: SMB 共有をマウントする（extras/smb）

Brick Pro の Linux には SMB（CIFS）も NFS もありませんが、FUSE は使えます。
Chrome 用の Ubuntu の中で [rclone](https://rclone.org/) を動かし、SMB 共有を読み取り専用でマウントします。
純正の音楽・写真・本のアプリは SD カードの Music / Pictures / Books しか見ないので、共有の中のフォルダをそこにも見せます。

Raspberry Pi 5 の Samba で動作を確認しました。Windows の共有フォルダは未確認です。

1. rclone（公式の arm64 版）と fuse3 を Ubuntu に入れる

   ```bash
   curl -fL -O https://downloads.rclone.org/rclone-current-linux-arm64.zip
   unzip rclone-current-linux-arm64.zip
   tools/brick-scp.exp rclone-*-linux-arm64/rclone /opt/brick-chrome/usr/local/bin/rclone
   tools/brick-run - <<'SH'
   chmod +x /opt/brick-chrome/usr/local/bin/rclone
   DEBIAN_FRONTEND=noninteractive chroot /opt/brick-chrome /usr/bin/apt-get install -y -qq fuse3
   SH
   ```

2. スクリプトと設定を送る。設定の `HOST`・`SMBUSER`・`BINDS` を自分の環境に合わせて書き換えてから送る

   ```bash
   tools/brick-scp.exp extras/smb/smb-mount.sh /opt/brick-chrome/smb-mount.sh
   tools/brick-scp.exp extras/smb/smb-mount.conf.example /mnt/UDISK/smb-mount.conf
   echo 'chmod +x /opt/brick-chrome/smb-mount.sh; chmod 600 /mnt/UDISK/smb-mount.conf' | tools/brick-run -
   ```

3. **root のパスワードを変える**（SMB のパスワードを本体に置くため）。PC から `ssh root@<IP>` でログインして `passwd`

4. SMB のパスワードを入れる（入力は画面に出ない。Brick には `stty` がないので Ubuntu の中のものを使う）

   ```bash
   ssh -t root@<IP> 'printf "SMB password: "; chroot /opt/brick-chrome /bin/stty -echo; read P; chroot /opt/brick-chrome /bin/stty echo; echo; O=$(chroot /opt/brick-chrome /usr/local/bin/rclone obscure "$P"); sed -i "s|^SMBPASS=.*|SMBPASS=$O|" /mnt/UDISK/smb-mount.conf && echo saved'
   ```

5. マウント: `ssh root@<IP> /opt/brick-chrome/smb-mount.sh start`（外すときは `stop`、確認は `status`）

   - サーバーの共有がすべて `/mnt/smb/` に並ぶ（純正の Video アプリは `/mnt/` から開ける）
   - `BINDS` に書いたフォルダが Music / Pictures / Books に出る

純正アプリの対応形式（アプリ本体の文字列から調べたもの）:

| アプリ | 対応 | 非対応 |
|---|---|---|
| Music | mp3, flac, wav, wma, ape | m4a（一覧に出ない） |
| Reader | zip, cbz, epub, pdf, mobi, txt | rar（cbr） |
| Video | mp4, mkv, avi | — |

## 起動スクリプト brickboot

起動時にスワップを有効にし、SMB 共有をマウントします。SD カードと内部ストレージのマウントを最大 2 分待ち、
SMB は Wi-Fi の接続を最大 1 分待ってから実行します。

```bash
tools/brick-scp.exp extras/brickboot/brickboot.init /etc/init.d/brickboot
echo 'chmod +x /etc/init.d/brickboot; /etc/init.d/brickboot enable' | tools/brick-run -
```

`/etc/init.d/` はシステム領域にあるので SD カードを替えても残りますが、ファームを更新すると消える可能性があります。
止めるときは `/etc/init.d/brickboot disable`。

## ライセンス

[MIT](LICENSE)。元の作者 vhu231 さんの著作権表示をそのまま残しています。
Chrome、Ubuntu、フォント、rclone はそれぞれのライセンスに従い、この repo では配布していません。
