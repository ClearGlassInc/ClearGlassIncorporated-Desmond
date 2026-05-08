# Authorization to Test (ATT) Template
## ClearGlass Detection Forge · Required Before Any Scenario Execution

---

> **This document must be completed, signed by all parties, and stored before any ClearGlass Detection Forge scenario is executed against any system or environment.**
>
> Executing adversary simulation scenarios without written authorization may violate the Computer Fraud and Abuse Act (18 U.S.C. § 1030), Canada's Criminal Code (s. 342.1), the Computer Misuse Act (UK), and equivalent legislation in your jurisdiction. ClearGlass Inc. and the platform authors accept zero liability for unauthorized use.

---

## AUTHORIZATION TO TEST DOCUMENT

**Document Reference:** ATT-____-CG-______  
**Version:** 1.0  
**Status:** [ ] DRAFT  [ ] SIGNED — AUTHORIZED  [ ] EXPIRED

---

### 1. Parties

**Authorizing Organization:**

| Field | Value |
|-------|-------|
| Legal Name | |
| Registered Address | |
| Primary Contact Name | |
| Primary Contact Title | |
| Primary Contact Email | |
| Primary Contact Phone | |

**Authorized Operator (ClearGlass or designated team):**

| Field | Value |
|-------|-------|
| Operator Name | |
| Operator Organization | |
| Operator Contact Email | |
| Operator Certifications | |

---

### 2. Scope of Authorization

**Authorized Target Systems:**

List all systems, IP ranges, hostnames, cloud accounts, or environments that are within scope. Any system NOT listed below is explicitly out of scope.

```
In Scope:
- IP Range / CIDR: ___________________________
- Hostnames:       ___________________________
- Cloud Accounts:  ___________________________
- Lab Environment: ___________________________
- Domain(s):       ___________________________

Explicitly Out of Scope:
- ____________________________________________
- ____________________________________________
```

**Environment Classification:**

[ ] Isolated lab environment (no production connectivity)  
[ ] Production-adjacent (limited blast radius controls in place)  
[ ] Production environment (senior executive sign-off required — see Section 6)  
[ ] Cloud environment (cloud provider notification may be required — see Section 7)

---

### 3. Authorized Activities

Check all that apply. Unchecked activities are NOT authorized under this document.

**Scenario Categories:**
- [ ] Initial Access simulation (TA0001)
- [ ] Execution emulation (TA0002)
- [ ] Persistence detection validation (TA0003)
- [ ] Privilege escalation emulation (TA0004)
- [ ] Defense evasion validation (TA0005)
- [ ] Discovery emulation (TA0007)
- [ ] Lateral movement emulation (TA0008)
- [ ] Collection simulation (TA0009)
- [ ] Command and control detection validation (TA0011)
- [ ] Exfiltration simulation (TA0010)

**Report Types:**
- [ ] Executive summary report
- [ ] Technical deep-dive report
- [ ] Compliance evidence pack
- [ ] STIX 2.1 bundle export

**Explicitly Prohibited (regardless of above selections):**
- [ ] No live malware deployment *(non-negotiable — always prohibited)*
- [ ] No actual credential capture *(non-negotiable — always prohibited)*
- [ ] No data destruction or encryption *(non-negotiable — always prohibited)*
- [ ] No persistence mechanisms that survive system reboot *(non-negotiable)*
- [ ] No exfiltration of real data *(non-negotiable — always prohibited)*

---

### 4. Authorized Time Window

| Parameter | Value |
|-----------|-------|
| Start Date & Time | |
| End Date & Time | |
| Authorized Time Zone | |
| Authorized Hours | (e.g., 09:00–17:00 ET weekdays only) |
| After-Hours Contact | |
| Emergency Stop Contact | |
| Emergency Stop Number | |

**Rules of Engagement for Out-of-Window Activity:**

All scenario execution must stop immediately if the authorized time window expires. Out-of-window execution requires written amendment to this document signed by the Authorizing Organization representative.

---

### 5. Notification and Communication

**Blue Team Awareness:**

[ ] Blue team is AWARE of the assessment (standard purple team)  
[ ] Blue team is NOT AWARE (blind assessment — requires additional senior sign-off)

**Incident Response Protocol:**

If any scenario execution causes unexpected system behavior, service degradation, or triggers an internal incident response process, the Authorized Operator will:

1. Immediately stop all scenario execution
2. Notify the Emergency Stop Contact within 15 minutes
3. Provide a full telemetry log of all actions taken
4. Cooperate fully with the IR team investigation

---

### 6. Production Environment Addendum

*Required if "Production environment" was selected in Section 2.*

Production environment assessments require additional authorization from:

| Role | Name | Signature |
|------|------|-----------|
| Chief Information Security Officer | | |
| Chief Technology Officer / CIO | | |
| Legal Counsel | | |

**Change Management Reference:** ____________________

**Rollback Plan Confirmed:** [ ] Yes  [ ] No *(must be Yes to proceed)*

---

### 7. Cloud Provider Notification

*Complete if cloud environments are in scope.*

Some cloud providers (AWS, Azure, GCP) require advance notification for penetration testing and adversary simulation. The Authorizing Organization confirms:

[ ] Cloud provider notification submitted and confirmed (attach reference)  
[ ] Cloud environment is a private lab with no provider notification required  
[ ] Legal counsel has confirmed no notification required for this scope

**Provider Notification Reference:** ____________________

---

### 8. Data Handling

All telemetry, log artifacts, and report outputs generated during this engagement are:

- Treated as confidential information of the Authorizing Organization
- Stored encrypted at rest (AES-256) and in transit (TLS 1.3)
- Retained for no more than 90 days post-engagement unless otherwise agreed
- Destroyed securely upon written request from the Authorizing Organization

**Report Delivery Method:** [ ] Encrypted email  [ ] Secure file transfer  [ ] In-person delivery

---

### 9. Signatures

By signing below, all parties confirm they have read, understood, and agree to the terms of this Authorization to Test document.

**Authorizing Organization Representative:**

```
Name:       ________________________________
Title:      ________________________________
Date:       ________________________________
Signature:  ________________________________
```

**Authorized Operator:**

```
Name:       ________________________________
Title:      ________________________________
Date:       ________________________________
Signature:  ________________________________
```

**CISO / Security Lead (if different from above):**

```
Name:       ________________________________
Title:      ________________________________
Date:       ________________________________
Signature:  ________________________________
```

---

### 10. ATT Token Generation

Upon execution of this document, generate an ATT token using:

```bash
python clearforge.py generate-att-token \
  --ref "ATT-2026-CG-XXXX" \
  --scope "lab-prod-01" \
  --expires "2026-06-01" \
  --authorized-by "Your Name"
```

Insert the generated token into `clearforge.config.yml` under `authorization.token`.

**No scenario will execute without a valid ATT token. This is enforced at the execution layer.**

---

*ClearGlass Inc. · Burlington, Ontario, Canada*  
*[clearglassinc.github.io/detection-forge.html](https://clearglassinc.github.io/detection-forge.html)*
