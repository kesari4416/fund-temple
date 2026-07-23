import { Fragment, useEffect, useRef, useState } from "react";
import { AiFillPrinter } from "react-icons/ai";
import { FaWhatsapp } from "react-icons/fa";
import { useReactToPrint } from "react-to-print";
import { useDispatch, useSelector } from "react-redux";
import { getManagement, selectManagementDetails } from "@modules/Management/ManagementSlice";
import { PrintWrapper } from "@components/common/Styled";
import { PrintHolder } from "@modules/Bill/Style";
import { Button } from "@components/form";
import { Flex } from "@components/others";
import axios from "axios";

// Collection categories that should NOT trigger the WhatsApp statement flow
// (chit-fund investors are not "members" in the tariff sense — they have
// their own settlement UX).
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

const ViewCollectionPrint = ({ CollectionRecord }) => {

  const dispatch = useDispatch();
  const componentRef = useRef();

  const [templeData, setTempleData] = useState([]);
  const [times, setTimes] = useState("");
  const [afterTime, setAfterTime] = useState("");
  const [waLoading, setWaLoading] = useState(false);
  const AllManagementDetails = useSelector(selectManagementDetails);

  const date = new Date();
  const showTime =
    date.getHours() + ":" + date.getMinutes() + ":" + date.getSeconds();

  useEffect(() => {
    setTimes(showTime)
  }, [showTime])

  useEffect(() => {
    dispatch(getManagement());
  }, []);

  useEffect(() => {
    setTempleData(AllManagementDetails);
  }, [AllManagementDetails]);

  const amount = parseFloat(CollectionRecord?.amount) || 0;
  const interestAmount = parseFloat(CollectionRecord?.interst_amount) || 0;
  const penaltyAmount = parseFloat(CollectionRecord?.penalty_amount) || 0;
  
  const TotalChitManagementAmt = amount + interestAmount + penaltyAmount;

  const memberId = CollectionRecord?.member;
  const rawMobile =
    CollectionRecord?.mobile_number || CollectionRecord?.mobile_no || "";
  // Only chit-fund investor categories are excluded from WhatsApp sharing –
  // for regular member Collections (Festival, Subscription Tariff, Death,
  // Marriage, …) we always show the button as long as we know which member
  // it belongs to. If the record itself doesn't carry a mobile number, we
  // fetch the member's saved mobile from the token endpoint.
  const canWhatsapp =
    !!memberId &&
    !WHATSAPP_SKIP_CATEGORIES.has(CollectionRecord?.collection_category);

  const handleWhatsappShare = async () => {
    if (!canWhatsapp || waLoading) return;
    setWaLoading(true);
    try {
      const { data } = await axios.get(
        `${API_BASE}/api/collection/member_statement/token/${memberId}/`
      );
      const link = buildStatementLink(data.token);
      const templeName = templeData?.temple_name || "our Temple";

      // Prefer the mobile stored on the collection record; fall back to the
      // member's saved mobile from the token response.
      const phone = String(rawMobile || data.mobile || "").replace(/\D/g, "");
      const waNumber = phone.length === 10 ? `91${phone}` : phone;
      if (waNumber.length < 10) {
        alert(
          "This member has no mobile number saved. Please update the member profile and try again."
        );
        return;
      }

      const paidAmt = (
        CollectionRecord?.collection_category === "Chit Interest" ||
        CollectionRecord?.collection_category === "Management Interest"
      )
        ? TotalChitManagementAmt
        : (CollectionRecord?.amount || 0);
      const msg = `Dear ${CollectionRecord?.member_name || data.name || "Member"}, thanks for your payment of \u20B9${paidAmt} on ${CollectionRecord?.pay_date}. View your 1-year account statement here: ${link} — ${templeName}`;
      const url = `https://wa.me/${waNumber}?text=${encodeURIComponent(msg)}`;
      window.open(url, "_blank", "noopener,noreferrer");
    } catch (e) {
      alert("Could not generate the statement link. Please try again.");
    } finally {
      setWaLoading(false);
    }
  };

  const handlePrint = useReactToPrint({
    content: () => componentRef.current,
    onAfterPrint: () => {
      const date = new Date();
      const newTime = date.getHours() + ":" + date.getMinutes() + ":" + date.getSeconds();
      setAfterTime(newTime);
    },
  });

  return (
    <Fragment>
      <Flex margin={"20px"} gap={"10px"}>
        <Button.Primary
          text={<AiFillPrinter style={{ fontSize: "30px" }} />}
          onClick={handlePrint}
          data-testid="collection-print-btn"
        />
        {canWhatsapp && (
          <Button.Primary
            text={
              waLoading
                ? "Sending..."
                : (
                  <span
                    style={{
                      display: "inline-flex",
                      alignItems: "center",
                      gap: 6,
                    }}
                  >
                    <FaWhatsapp style={{ fontSize: "22px" }} />
                    Share Statement
                  </span>
                )
            }
            onClick={handleWhatsappShare}
            data-testid="collection-whatsapp-btn"
          />
        )}
      </Flex>
      <PrintWrapper>
        <PrintHolder ref={componentRef}>
          <div className="container">
            <div className="address">
              <h1>{templeData?.temple_name}</h1>
              <h2>{templeData?.address}</h2>
              {/* <h2>Ph.no: 854345666</h2> */}
            </div>
            <div className="bill_details">
              <div className="holder">
                <h4>Date: {CollectionRecord?.pay_date}</h4>
                <h4>Bill No :&nbsp;{CollectionRecord?.collaction_no} </h4>
              </div>
              <div className="holder">
                <h4>Time : {times || afterTime}</h4>
                <h4>
                  Bill&nbsp;by:&nbsp;
                  {CollectionRecord?.bill_by_name}
                </h4>
              </div>
             
            </div>
            <div className="down_holder">
                <h4>Bill&nbsp;to: &nbsp;{CollectionRecord?.member_name}</h4>
                <h4>Mob No: &nbsp;{CollectionRecord?.mobile_number || CollectionRecord?.mobile_no}</h4>
              </div>
            <div className="table_holder">
              <table>
                <thead>
                  <tr>
                    <th>S. No</th>
                    <th>Particulars</th>
                    {CollectionRecord?.collection_category !== "Management Interest" && <th>Name</th>}
                    <th>Amount</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>1.</td>
                    <td>{CollectionRecord?.collection_category}</td>
                    {CollectionRecord?.collection_category === "Festival" && <td>{CollectionRecord?.festival_name}</td>}
                    {CollectionRecord?.collection_category === "Marriage" && <td>{CollectionRecord?.marriage_name}</td>}
                    {CollectionRecord?.collection_category === "Death Tariff" && <td>{CollectionRecord?.death_name}</td>}
                    {CollectionRecord?.collection_category === "Subscription Tariff" && <td>{CollectionRecord?.sub_tariff_no}</td>}
                    {CollectionRecord?.collection_category === "Rent" && <td>{CollectionRecord?.rent_name}</td>}
                    {CollectionRecord?.collection_category === "Lease" && <td>{CollectionRecord?.lease_name}</td>}
                    {CollectionRecord?.collection_category === "Moveable Rent" && <td>{CollectionRecord?.moveable_rent_name}</td>}
                    {CollectionRecord?.collection_category === "Balance" && <td>{CollectionRecord?.balance_name}</td>}
                    {CollectionRecord?.collection_category === "Fund" && <td>{CollectionRecord?.fund_name}</td>}
                    {CollectionRecord?.collection_category === "Chit Interest" && <td>{CollectionRecord?.chit_name}</td>}

                    <td>{(CollectionRecord?.collection_category === "Chit Interest" || CollectionRecord?.collection_category === "Management Interest") ?TotalChitManagementAmt: CollectionRecord?.amount}</td>
                  </tr>
                </tbody>
              </table>
            </div>

            <div className="amount_holder">
              <h2>Amount: ₹&nbsp;{(CollectionRecord?.collection_category === "Chit Interest" || CollectionRecord?.collection_category === "Management Interest") ?TotalChitManagementAmt: CollectionRecord?.amount}</h2>
            </div>
          </div>
        </PrintHolder>
      </PrintWrapper>
    </Fragment>
  );
};
export default ViewCollectionPrint;
