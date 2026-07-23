import { useState } from "react";
import { FaWhatsapp } from "react-icons/fa";
import axios from "axios";
import { Button } from "@components/form";

// Collection categories that must NOT trigger the WhatsApp statement flow.
// Chit-fund investors have their own settlement UX; interest lines aren't
// tied to a Member either.
const WHATSAPP_SKIP_CATEGORIES = new Set([
  "Chit-fund",
  "Chit Interest",
  "Management Interest",
]);

const API_BASE =
  import.meta.env?.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || "";

const buildStatementLink = (token) => {
  const origin =
    typeof window !== "undefined" && window.location?.origin
      ? window.location.origin
      : "";
  return `${origin}/statement/${token}`;
};

/**
 * Renders a "Share Statement" WhatsApp button that opens wa.me with a
 * pre-filled message linking to the member's public 1-year statement page.
 * Silently renders nothing when the collection cannot be shared
 * (missing memberId / chit category).
 */
const WhatsappStatementButton = ({ CollectionRecord, templeName }) => {
  const [loading, setLoading] = useState(false);

  const memberId = CollectionRecord?.member;
  const category = CollectionRecord?.collection_category;

  if (!memberId || WHATSAPP_SKIP_CATEGORIES.has(category)) {
    return null;
  }

  const rawMobile =
    CollectionRecord?.mobile_number || CollectionRecord?.mobile_no || "";

  const amount = parseFloat(CollectionRecord?.amount) || 0;
  const interestAmount = parseFloat(CollectionRecord?.interst_amount) || 0;
  const penaltyAmount = parseFloat(CollectionRecord?.penalty_amount) || 0;
  const chitOrMgmtTotal = amount + interestAmount + penaltyAmount;
  const paidAmt =
    category === "Chit Interest" || category === "Management Interest"
      ? chitOrMgmtTotal
      : amount;

  const handleClick = async () => {
    if (loading) return;
    setLoading(true);
    try {
      const { data } = await axios.get(
        `${API_BASE}/api/collection/member_statement/token/${memberId}/`
      );
      const link = buildStatementLink(data.token);
      const phone = String(rawMobile || data.mobile || "").replace(/\D/g, "");
      const waNumber = phone.length === 10 ? `91${phone}` : phone;
      if (waNumber.length < 10) {
        alert(
          "This member has no mobile number saved. Please update the member profile and try again."
        );
        return;
      }
      const name = CollectionRecord?.member_name || data.name || "Member";
      const msg = `Dear ${name}, thanks for your payment of \u20B9${paidAmt} on ${CollectionRecord?.pay_date}. View your 1-year account statement here: ${link} — ${templeName || "our Temple"}`;
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
