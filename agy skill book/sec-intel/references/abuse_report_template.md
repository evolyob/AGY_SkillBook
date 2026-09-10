# Standard Abuse & Takedown Notification Templates

This reference defines authoritative, parameterized email notification templates for reporting abusive domains, phishing websites, IP attacks, and brand impersonation to Registrars, Web Hosts, and Cloud Service Providers.

---

## Template 1: Domain Phishing & Brand Impersonation Takedown Notice

Use when reporting fraudulent domains, spoofed websites, and fake login portals to Domain Registrars.

### Metadata
- **To**: `<REGISTRAR_ABUSE_EMAIL>`
- **Subject**: `Abuse Report: Phishing / Brand Impersonation on <OFFENDING_DOMAIN_DEFANGED>`

### Body Content
```text
<REGISTRAR_NAME> Abuse Team,

We detected active credential phishing hosted on <OFFENDING_DOMAIN_DEFANGED>, registered through <REGISTRAR_NAME>. The spoofed portal copies our official corporate branding (<ORGANIZATION_NAME>) to harvest customer authentication credentials.

Incident Details:
• Malicious URL    : <MALICIOUS_URL_DEFANGED>
• Target Brand     : <OFFICIAL_DOMAIN> (<ORGANIZATION_NAME>)
• Attack Type      : Credential Phishing / Brand Impersonation
• First Observed   : <YYYY-MM-DD HH:MM> UTC

Attached Evidence (<EVIDENCE_FILENAME.pdf>):
1. Full-page screenshot with address bar and fake login interface.
2. Side-by-side comparison with our official site (<OFFICIAL_URL>).
3. Raw phishing email headers (if delivered via email).

Please investigate and suspend domain resolution under your abuse policy and ICANN RAA §3.18.2 obligations.

Please confirm receipt and provide a ticket reference.

Regards,

<REPORTER_NAME>
Security Operations Team
<ORGANIZATION_NAME>
Contact: <SECURITY_CONTACT_EMAIL>
```

---

## Template 2: Malicious IP Attack & Unauthorized Scanning Notice

Use when reporting malicious IP activities (brute-force, port scanning, C2 traffic, vulnerability exploitation) to Cloud / ISP Abuse Teams.

### Metadata
- **To**: `<ISP_OR_CLOUD_ABUSE_EMAIL>`
- **Subject**: `Abuse Report: <INCIDENT_TYPE> originating from <OFFENDING_IP> - <YYYY-MM-DD UTC>`

### Body Content
```text
<PROVIDER_NAME> Abuse Team,

The Security Operations Center at <ORGANIZATION_NAME> detected malicious traffic originating from <OFFENDING_IP> on your network:

• Offending IP     : <OFFENDING_IP>
• Incident Type    : <Vulnerability Scanning / SSH Brute-Force / C2 Beaconing>
• Activity Window  : <YYYY-MM-DD HH:MM:SS UTC> to <YYYY-MM-DD HH:MM:SS UTC>
• Targeted Asset   : <TARGET_IP_OR_HOSTNAME> (<PORT>/<PROTO>)

Evidence Logs:
```
<PASTE_RELEVANT_VERBATIM_LOG_LINES_HERE>
```

Under your Acceptable Use Policy (AUP), please:
1. Isolate the offending host or tenant account.
2. Stop the outbound malicious traffic.
3. Reply with your internal tracking ticket ID.

Thank you for your assistance.

<REPORTER_NAME>
SOC Team, <ORGANIZATION_NAME>
Contact: <SECURITY_CONTACT_EMAIL>
```

---

## Template 3: 請求 TWNIC 啟動 DNS RPZ 停止解析通報信 (台灣專用)

用於向 TWNIC 濫用防制小組舉報涉詐偽冒釣魚網域，請求依《打詐專法》及《運用 DNS RPZ 自律機制停止解析違法網站處理參考程序》執行全台 DNS 域名停止解析阻斷。

### 必要提供資料檢核清單 (Mandatory Information Checklist)
1. **通報受害主體**：企業名稱、統一編號、資安或法務權責人員姓名、官方聯絡電話及企業信箱。
2. **涉詐精確網域名稱 (FQDN)**：標的 FQDN（例：`login.fake-brand[.]com`），若整網域皆為偽冒需特別註明。
3. **解析 IP 與真實惡意 URL**：含參數之完整惡意 URL（需 Defang），及當前 DNS 解析之 IP 與 Hosting 業者。
4. **被偽冒之正版身分**：官方正確網址與商標註冊證號或在法營運證明。
5. **不可否認之客觀事證（PDF 附檔）**：
   - 偽冒登入頁全螢幕截圖（需清晰呈現瀏覽器網址列與完整 URL）。
   - 正版官網外觀對照截圖。
   - 受害民眾檢舉之釣魚簡訊/信件截圖（含寄件者來源）。
6. **法源與請求主旨**：明列依據《詐欺犯罪危害防制條例》第 41 條、《運用 DNS RPZ 自律機制停止解析違法網站處理參考程序》，建請協調各大 IASP 執行停止解析。

### Metadata
- **To**: `abuse@twnic.tw`
- **線上通報管道 (若需 165 警政立案)**: [165 全民防騙網 (165.npa.gov.tw)](https://165.npa.gov.tw) / [數發部網路詐騙通報查詢網](https://fraudbuster.digiat.org.tw)
- **Subject**: `【緊急資安通報】請求對涉詐釣魚網域 <OFFENDING_FQDN_DEFANGED> 啟動 DNS RPZ 停止解析`

### Body Content
```text
TWNIC 濫用防制小組您好：

本公司（<ORGANIZATION_NAME>，統編：<ORGANIZATION_ID>）監控發現有釣魚網站冒用本公司品牌，誘騙民眾輸入帳號密碼與個資。

為避免損害擴大，特檢附完整事證，建請 貴中心依《詐欺犯罪危害防制條例》第 41 條及《運用 DNS RPZ 自律機制停止解析違法網站處理參考程序》，協助將該網域納入 DNS RPZ 停止解析，阻斷境內連線。本案已同步至 165 全民防騙網線上檢舉立案（案號：<165_REPORT_NO_IF_AVAILABLE>）。

【涉案網域與情資】
1. 涉詐 FQDN        : <OFFENDING_FQDN_DEFANGED>
2. 完整惡意 URL      : <MALICIOUS_URL_DEFANGED>
3. 解析 IP 與機房   : <OFFENDING_IP> (ASN: <ASN_NUMBER>, 主機商: <HOSTING_PROVIDER>)
4. 發現時間 (UTC+8) : <YYYY-MM-DD HH:MM:SS>
5. 遭偽冒官方網址   : <OFFICIAL_WEBSITE_URL> (商標註冊證號: <TRADEMARK_REG_NO>)
6. 違法危害型態     : <假冒會員登入 / 騙取信用卡 / 偽冒繳費>

【客觀事證附件】(詳見檢附之 <EVIDENCE_FILENAME.pdf>)
• 附件一：釣魚網站全螢幕截圖（含完整網址列與假登入表單）。
• 附件二：本公司正版官網比對截圖。
• 附件三：民眾檢舉之詐騙簡訊 / 釣魚郵件截圖。
• 附件四：商標註冊證影本及公司證明文件。

若需補充任何資料，請隨時聯繫本案窗口。感謝協助！

通報單位：<ORGANIZATION_NAME> 資安團隊
聯絡人　：<REPORTER_NAME> (<JOB_TITLE>)
聯絡電話：<CONTACT_PHONE>
官方信箱：<SECURITY_CONTACT_EMAIL>
中華民國 <民國年> 年 <MM> 月 <DD> 日
```

---

## Defanging Guidelines
Before dispatching, ensure all malicious targets are defanged in plain text to prevent security filtering or accidental navigation:
- Replace `.` with `[.]` (e.g. `example-phishing[.]com`)
- Replace `http` with `hxxp` / `https` with `hxxps`

