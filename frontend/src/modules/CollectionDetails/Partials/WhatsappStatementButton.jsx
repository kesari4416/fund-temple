import { useState } from "react";
import { FaWhatsapp } from "react-icons/fa";
import axios from "axios";
import { Button } from "@components/form";

// Collection categories that share a per-interest-loan statement instead of
// the per-Member one. These typically carry a NULL `member` FK but a valid
// `interest` FK, so we resolve them via the borrower's interest record.
const INTEREST_CATEGORIES = new Set(["Chit Interest", "Management Interest"]);

const API_BASE =
  import.meta.env?.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || "";

const buildMemberStatementLink = (token) => {
  const origin =
    typeof window !== "undefined" && window.location?.origin
      ? window.location.origin
      : "";
  return `${origin}/statement/${token}`;
};

const buildInterestStatementLink = (token) => {
  const origin =
    typeof window !== "undefined" && window.location?.origin
      ? window.location.origin
      : "";
  return `${origin}/interest-statement/${token}`;
};

/**
 * "Share Statement" WhatsApp button.
 * - For regular collections: opens the per-Member 1-year statement.
 * - For Management Interest / Chit Interest: opens the per-loan statement
 *   (via the CollectionRecord.interest FK) — supports borrowers who are
 *   NOT Members (people_type = "Other").
 * - For Chit-fund settlement / investor rows we still skip (they have their
 *   own settlement UX).
 */
const WhatsappStatementButton = ({ CollectionRecord, templeName }) => {
  const [loading, setLoading] = useState(false);

  const category = CollectionRecord?.collection_category;
  const memberId = CollectionRecord?.member;
  const interestId = CollectionRecord?.interest;

  // Chit-fund settlement rows are excluded (no per-payer statement).
  if (category === "Chit-fund") return null;

  const isInterest = INTEREST_CATEGORIES.has(category);
  // Interest rows must have an interest FK; everything else must have a
  // member FK. If neither is present, the button cannot resolve a payer.
  if (isInterest && !interestId) return null;
  if (!isInterest && !memberId) return null;

  const rawMobile =
    CollectionRecord?.mobile_number || CollectionRecord?.mobile_no || "";

  const amount = parseFloat(CollectionRecord?.amount) || 0;
  const interestAmount = parseFloat(CollectionRecord?.interst_amount) || 0;
  const penaltyAmount = parseFloat(CollectionRecord?.penalty_amount) || 0;
  const paidAmt = isInterest
    ? amount + interestAmount + penaltyAmount
    : amount;

  const handleClick = async () => {
    if (loading) return;
    setLoading(true);
    try {
      let link;
      let fallbackName;
      let fallbackMobile;
      if (isInterest) {
        const { data } = await axios.get(
          `${API_BASE}/api/collection/interest_statement/token/${interestId}/`
        );
        link = buildInterestStatementLink(data.token);
        fallbackName = data.name;
        fallbackMobile = data.mobile;
      } else {
        const { data } = await axios.get(
          `${API_BASE}/api/collection/member_statement/token/${memberId}/`
        );
        link = buildMemberStatementLink(data.token);
        fallbackName = data.name;
        fallbackMobile = data.mobile;
      }
      const phone = String(rawMobile || fallbackMobile || "").replace(/\D/g, "");
      const waNumber = phone.length === 10 ? `91${phone}` : phone;
      if (waNumber.length < 10) {
        alert(
          "No mobile number is saved for this record. Please update the profile and try again."
        );
        return;
      }
      const name =
        CollectionRecord?.member_name || fallbackName || "Customer";
      const msg = `Dear ${name}, thanks for your payment of \u20B9${paidAmt} on ${CollectionRecord?.pay_date}. View your 1-year statement here: ${link} — ${templeName || "our Temple"}`;
      const url = `https://wa.me/${waNumber}?text=${encodeURIComponent(msg)}`;
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (e) {
      alert("Could not generate the statement link. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button.Primary
      text={
        loading ? (
          "Sending..."
        ) : (
          <span style={{ display: "inline-flex", alignItems: "center", gap: 6 }}>
            <FaWhatsapp style={{ fontSize: "22px" }} />
            Share Statement
          </span>
        )
      }
      onClick={handleClick}
      data-testid="collection-whatsapp-btn"
    />
  );
};

export default WhatsappStatementButton;
