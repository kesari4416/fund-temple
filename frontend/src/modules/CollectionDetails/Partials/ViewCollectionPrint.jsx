import { Fragment, useEffect, useMemo, useRef, useState } from "react";
import { AiFillPrinter } from "react-icons/ai";
import { useReactToPrint } from "react-to-print";
import { useDispatch, useSelector } from "react-redux";
import axios from "axios";
import { getManagement, selectManagementDetails } from "@modules/Management/ManagementSlice";
import { PrintWrapper } from "@components/common/Styled";
import { PrintHolder } from "@modules/Bill/Style";
import { Button } from "@components/form";
import { Flex } from "@components/others";
import WhatsappStatementButton from "./WhatsappStatementButton";

const API_BASE =
  import.meta.env?.VITE_BACKEND_URL || process.env.REACT_APP_BACKEND_URL || "";

const INTEREST_CATEGORIES = new Set(["Chit Interest", "Management Interest"]);

const fmtAmt = (n) => Number(n || 0).toFixed(2);

const StatementTableBlock = ({ statement, isInterest }) => {
  const rows = statement?.collections || [];
  const t = statement?.totals || {};
  const outstanding = statement?.outstanding;
  const pendingTotal =
    !isInterest && statement?.pending_dues && statement.pending_dues.Total !== undefined
      ? Number(statement.pending_dues.Total || 0)
      : null;

  return (
    <div>
      {rows.length === 0 ? (
        <div style={{ fontSize: 13, color: "#64748b" }}>
          No payments in the last 12 months.
        </div>
      ) : (
        <div style={{ overflowX: "auto" }}>
          <table
            data-testid="inline-statement-table"
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: 12,
              fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
            }}
          >
            <thead>
              <tr style={{ background: "#f8fafc", color: "#0f172a" }}>
                <th style={{ padding: "8px 10px", textAlign: "left", borderBottom: "1px solid #e2e8f0" }}>Date</th>
                <th style={{ padding: "8px 10px", textAlign: "left", borderBottom: "1px solid #e2e8f0" }}>Category</th>
                <th style={{ padding: "8px 10px", textAlign: "right", borderBottom: "1px solid #e2e8f0" }}>Amt</th>
                <th style={{ padding: "8px 10px", textAlign: "right", borderBottom: "1px solid #e2e8f0" }}>Pen</th>
                <th style={{ padding: "8px 10px", textAlign: "right", borderBottom: "1px solid #e2e8f0" }}>Running</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} data-testid={`inline-statement-row-${r.id}`}>
                  <td style={{ padding: "6px 10px", borderBottom: "1px solid #f1f5f9" }}>{r.date || "-"}</td>
                  <td style={{ padding: "6px 10px", borderBottom: "1px solid #f1f5f9" }}>{r.category || "-"}</td>
                  <td style={{ padding: "6px 10px", textAlign: "right", borderBottom: "1px solid #f1f5f9" }}>{fmtAmt(r.amount)}</td>
                  <td style={{ padding: "6px 10px", textAlign: "right", borderBottom: "1px solid #f1f5f9", color: Number(r.penalty_amount || 0) > 0 ? "#b91c1c" : "#0f172a" }}>{fmtAmt(r.penalty_amount)}</td>
                  <td style={{ padding: "6px 10px", textAlign: "right", borderBottom: "1px solid #f1f5f9", fontWeight: 600 }}>{fmtAmt(r.running_total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div style={{ marginTop: 10, fontSize: 12, color: "#0f172a" }}>
        <div data-testid="inline-statement-total">
          Total received (1 yr): <strong>₹{fmtAmt(t.amount)}</strong> · {t.count || 0} payments
        </div>
        {isInterest && outstanding && (
          <div data-testid="inline-statement-outstanding" style={{ marginTop: 4 }}>
            Outstanding: Principal <strong>₹{fmtAmt(outstanding.principal_balance)}</strong> ·
            Penalty <strong>₹{fmtAmt(outstanding.penalty_balance_amt)}</strong> ={" "}
            <strong style={{ color: "#b91c1c" }}>
              ₹{fmtAmt(Number(outstanding.balance_amt || 0) + Number(outstanding.penalty_balance_amt || 0))}
            </strong>
          </div>
        )}
        {!isInterest && pendingTotal !== null && pendingTotal > 0 && (
          <div data-testid="inline-statement-pending" style={{ marginTop: 4 }}>
            Pending dues: <strong style={{ color: "#b91c1c" }}>₹{fmtAmt(pendingTotal)}</strong>
          </div>
        )}
      </div>
    </div>
  );
};

const ViewCollectionPrint = ({ CollectionRecord }) => {

  const dispatch = useDispatch();
  const componentRef = useRef();

  const [templeData, setTempleData] = useState([]);
  const [times, setTimes] = useState("");
  const [afterTime, setAfterTime] = useState("");
  const AllManagementDetails = useSelector(selectManagementDetails);

  // -------- 1-year balance sheet (in-modal dashboard view) --------
  const [statement, setStatement] = useState(null);
  const [statementLoading, setStatementLoading] = useState(false);
  const [statementError, setStatementError] = useState(null);

  const category = CollectionRecord?.collection_category;
  const isInterest = INTEREST_CATEGORIES.has(category);
  const canShowStatement =
    (isInterest && CollectionRecord?.interest) ||
    (!isInterest && CollectionRecord?.member);

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

  // Fetch the 1-year balance sheet on mount so it's ready to display
  // inline. Uses the same public statement endpoints the WhatsApp link
  // would have used, so the numbers match exactly.
  useEffect(() => {
    if (!canShowStatement) return;
    let cancelled = false;
    (async () => {
      try {
        setStatementLoading(true);
        setStatementError(null);
        let tokenUrl;
        let publicUrl;
        if (isInterest) {
          const { data } = await axios.get(
            `${API_BASE}/api/collection/interest_statement/token/${CollectionRecord.interest}/`
          );
          tokenUrl = data.token;
          publicUrl = `${API_BASE}/api/collection/public/interest_statement/${tokenUrl}/`;
        } else {
          const { data } = await axios.get(
            `${API_BASE}/api/collection/member_statement/token/${CollectionRecord.member}/`
          );
          tokenUrl = data.token;
          publicUrl = `${API_BASE}/api/collection/public/member_statement/${tokenUrl}/`;
        }
        const { data: stmt } = await axios.get(publicUrl);
        if (!cancelled) setStatement(stmt);
      } catch (err) {
        if (!cancelled)
          setStatementError("Could not load 1-year balance sheet.");
      } finally {
        if (!cancelled) setStatementLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [canShowStatement, isInterest, CollectionRecord?.interest, CollectionRecord?.member]);

  const amount = parseFloat(CollectionRecord?.amount) || 0;
  const interestAmount = parseFloat(CollectionRecord?.interst_amount) || 0;
  const penaltyAmount = parseFloat(CollectionRecord?.penalty_amount) || 0;
  
  const TotalChitManagementAmt = amount + interestAmount + penaltyAmount;

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
        <WhatsappStatementButton
          CollectionRecord={CollectionRecord}
          templeName={templeData?.temple_name}
        />
      </Flex>

      {canShowStatement && (
        <div
          data-testid="inline-balance-sheet"
          style={{
            margin: "0 20px 20px 20px",
            border: "1px solid #e2e8f0",
            borderRadius: 10,
            background: "#fff",
            padding: 16,
            fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            color: "#0f172a",
          }}
        >
          <div style={{ fontWeight: 700, marginBottom: 8, color: "#0F5132" }}>
            1-year balance sheet
          </div>
          {statementLoading && <div style={{ fontSize: 13 }}>Loading…</div>}
          {statementError && (
            <div style={{ fontSize: 13, color: "#b91c1c" }}>{statementError}</div>
          )}
          {!statementLoading && !statementError && statement && (
            <StatementTableBlock statement={statement} isInterest={isInterest} />
          )}
        </div>
      )}

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
