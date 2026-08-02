import { useEffect, useMemo, useState } from "react";
import { useParams, Link } from "react-router-dom";
import styled from "styled-components";
import request from "@request/request";

const Wrap = styled.div`
  min-height: 100vh;
  background: #f8fafc;
  padding: 24px 24px 60px 24px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
  color: #0f172a;
`;

const HeaderBar = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 20px;
`;

const Title = styled.h1`
  margin: 0;
  font-size: 22px;
  color: #7f1d1d;
`;

const Subtitle = styled.div`
  font-size: 13px;
  color: #64748b;
  margin-top: 4px;
`;

const Card = styled.div`
  background: #ffffff;
  border-radius: 12px;
  padding: 16px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
  overflow-x: auto;
`;

const SummaryGrid = styled.div`
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
`;

const Stat = styled.div`
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  padding: 12px 14px;
  small { color: #64748b; font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; }
  strong { display: block; font-size: 18px; margin-top: 4px; color: #0f172a; }
`;

const Toolbar = styled.div`
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
  input, select, button {
    padding: 8px 12px;
    border-radius: 8px;
    border: 1px solid #cbd5e1;
    font-size: 13px;
    background: #fff;
  }
  input { min-width: 240px; }
  button {
    cursor: pointer;
    background: #b91c1c;
    color: #fff;
    border-color: #b91c1c;
    font-weight: 600;
  }
  button.secondary {
    background: #fff;
    color: #0f172a;
    border-color: #cbd5e1;
    font-weight: 500;
  }
`;

const Table = styled.table`
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  th, td { padding: 10px 12px; border: 1px solid #e2e8f0; text-align: left; }
  th { background: #fee2e2; color: #7f1d1d; font-weight: 700; position: sticky; top: 0; }
  tbody tr:nth-child(even) td { background: #fafafa; }
  td.num { text-align: right; white-space: nowrap; }
  td.bal { color: #b91c1c; font-weight: 700; }
  a { color: #0f5132; text-decoration: none; }
  a:hover { text-decoration: underline; }
`;

const fmt = (n) => Number(n || 0).toFixed(2);

const ChitFundPendingBorrowersPage = () => {
  const { id } = useParams();
  const [state, setState] = useState({ loading: true, error: null, data: null });
  const [query, setQuery] = useState("");
  const [sortKey, setSortKey] = useState("weeks_from_start");
  const [sortDir, setSortDir] = useState("desc");

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const resp = await request.get(`chit_fund/pending_borrowers/${id}/`);
        if (!cancelled) setState({ loading: false, error: null, data: resp.data });
      } catch (err) {
        if (!cancelled)
          setState({
            loading: false,
            error:
              err?.response?.data?.detail ||
              "Could not load pending borrowers.",
            data: null,
          });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [id]);

  const rows = useMemo(() => {
    if (!state.data?.borrowers) return [];
    const q = query.trim().toLowerCase();
    let filtered = state.data.borrowers.filter((b) =>
      !q ||
      (b.name || "").toLowerCase().includes(q) ||
      (b.mobile || "").toLowerCase().includes(q)
    );
    filtered = [...filtered].sort((a, b) => {
      const av = a[sortKey] ?? 0;
      const bv = b[sortKey] ?? 0;
      if (typeof av === "number" && typeof bv === "number") {
        return sortDir === "asc" ? av - bv : bv - av;
      }
      return sortDir === "asc"
        ? String(av).localeCompare(String(bv))
        : String(bv).localeCompare(String(av));
    });
    return filtered;
  }, [state.data, query, sortKey, sortDir]);

  const toggleSort = (key) => {
    if (sortKey === key) setSortDir(sortDir === "asc" ? "desc" : "asc");
    else {
      setSortKey(key);
      setSortDir("desc");
    }
  };

  const handlePrint = () => window.print();

  const handleWhatsappReminder = (b) => {
    const phone = String(b.mobile || "").replace(/\D/g, "");
    const waNumber = phone.length === 10 ? `91${phone}` : phone;
    if (waNumber.length < 10) {
      alert("No mobile number saved for this borrower.");
      return;
    }
    const msg = `Reminder: ₹${fmt(b.balance_amt)} is pending on your ${b.interest_type} loan (start ${b.start_date}, ${b.weeks_from_start ?? "-"} weeks). Please clear at the earliest.`;
    window.open(
      `https://wa.me/${waNumber}?text=${encodeURIComponent(msg)}`,
      "_blank",
      "noopener,noreferrer"
    );
  };

  if (state.loading)
    return (
      <Wrap data-testid="pending-borrowers-loading">
        <Card>Loading pending borrowers…</Card>
      </Wrap>
    );
  if (state.error)
    return (
      <Wrap data-testid="pending-borrowers-error">
        <Card>
          <Title>Could not load</Title>
          <Subtitle>{state.error}</Subtitle>
        </Card>
      </Wrap>
    );

  const d = state.data;

  return (
    <Wrap data-testid="pending-borrowers-root">
      <HeaderBar>
        <div>
          <Title data-testid="pending-borrowers-title">
            Pending borrowers — {d.chit_name}
          </Title>
          <Subtitle>
            Chit ID #{d.chit_id} · Principal given ₹{fmt(d.principal_given_amount)} · Collected ₹{fmt(d.collected_principal_amount)}
          </Subtitle>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <Link
            to={`/chitfundListView/${id}`}
            style={{
              padding: "8px 14px",
              borderRadius: 8,
              border: "1px solid #cbd5e1",
              background: "#fff",
              color: "#0f172a",
              fontWeight: 500,
              textDecoration: "none",
              fontSize: 13,
            }}
            data-testid="pending-borrowers-back"
          >
            ← Back to Chit Fund
          </Link>
        </div>
      </HeaderBar>

      <SummaryGrid>
        <Stat data-testid="pending-summary-count">
          <small>Pending borrowers</small>
          <strong>{d.count}</strong>
        </Stat>
        <Stat data-testid="pending-summary-principal">
          <small>Total Principal</small>
          <strong>₹ {fmt(d.total_pending_principal)}</strong>
        </Stat>
        <Stat data-testid="pending-summary-interest">
          <small>Total Interest</small>
          <strong>₹ {fmt(d.total_pending_interest)}</strong>
        </Stat>
        <Stat data-testid="pending-summary-balance">
          <small>Total outstanding (incl. penalty)</small>
          <strong style={{ color: "#b91c1c" }}>₹ {fmt(d.total_pending_balance)}</strong>
        </Stat>
      </SummaryGrid>

      <Toolbar>
        <input
          type="search"
          placeholder="Search by name or mobile…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          data-testid="pending-borrowers-search"
        />
        <select
          value={`${sortKey}:${sortDir}`}
          onChange={(e) => {
            const [k, d2] = e.target.value.split(":");
            setSortKey(k);
            setSortDir(d2);
          }}
          data-testid="pending-borrowers-sort"
        >
          <option value="weeks_from_start:desc">Oldest first (weeks from start)</option>
          <option value="weeks_from_start:asc">Newest first</option>
          <option value="weeks_from_last_payment:desc">Longest overdue (weeks since last pay)</option>
          <option value="balance_amt:desc">Highest balance first</option>
          <option value="balance_amt:asc">Lowest balance first</option>
          <option value="name:asc">Name A → Z</option>
        </select>
        <button className="secondary" onClick={handlePrint} data-testid="pending-borrowers-print">
          Print
        </button>
      </Toolbar>

      <Card>
        {rows.length === 0 ? (
          <div data-testid="pending-borrowers-empty" style={{ padding: 20, color: "#64748b" }}>
            No borrowers match your filter.
          </div>
        ) : (
          <Table data-testid="pending-borrowers-table">
            <thead>
              <tr>
                <th>#</th>
                <th onClick={() => toggleSort("name")} style={{ cursor: "pointer" }}>Borrower ▲▼</th>
                <th>Interest type</th>
                <th onClick={() => toggleSort("start_date")} style={{ cursor: "pointer" }}>Start</th>
                <th>End</th>
                <th className="num" onClick={() => toggleSort("weeks_from_start")} style={{ cursor: "pointer" }} title="Weeks since loan started">Weeks (start)</th>
                <th className="num" onClick={() => toggleSort("weeks_from_last_payment")} style={{ cursor: "pointer" }} title="Weeks since the borrower's most recent payment (only starts counting after the first collection)">Weeks (since last pay)</th>
                <th className="num" title="Principal only">Principal</th>
                <th className="num" title="From interest master: final_amt_given">Final amount given</th>
                <th className="num" title="Interest charged on the loan">Interest</th>
                <th className="num">Interest paid</th>
                <th className="num" title="Per-cycle penalty amount (installment_amt × penalty %)">Penalty bal</th>
                <th className="num" onClick={() => toggleSort("balance_amt")} style={{ cursor: "pointer" }}>Balance</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((b, i) => (
                <tr key={b.id} data-testid={`pending-borrowers-row-${b.id}`}>
                  <td>{i + 1}</td>
                  <td>
                    <div style={{ fontWeight: 600 }}>{b.name || "-"}</div>
                    {b.mobile ? (
                      <div style={{ fontSize: 11, color: "#64748b" }}>{b.mobile}</div>
                    ) : null}
                  </td>
                  <td>{b.interest_type || "-"}</td>
                  <td>{b.start_date || "-"}</td>
                  <td>{b.end_date || "-"}</td>
                  <td className="num">{b.weeks_from_start ?? "-"}</td>
                  <td className="num">{b.weeks_from_last_payment ?? "-"}</td>
                  <td className="num">₹ {fmt(b.principal_amt)}</td>
                  <td className="num">₹ {fmt(b.final_amt_given)}</td>
                  <td className="num">₹ {fmt(b.interest_amt)}</td>
                  <td className="num">₹ {fmt(b.interest_paid)}</td>
                  <td className="num">₹ {fmt(b.penalty_balance_amt)}</td>
                  <td className="num bal" data-testid={`pending-borrowers-row-${b.id}-balance`}>
                    ₹ {fmt(b.balance_amt)}
                  </td>
                  <td>
                    <button
                      className="secondary"
                      style={{
                        padding: "4px 10px",
                        fontSize: 11,
                        background: "#25D366",
                        color: "#fff",
                        borderColor: "#25D366",
                        border: "1px solid",
                        borderRadius: 6,
                        cursor: "pointer",
                        fontWeight: 600,
                      }}
                      onClick={() => handleWhatsappReminder(b)}
                      data-testid={`pending-borrowers-row-${b.id}-remind`}
                    >
                      Remind
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>
    </Wrap>
  );
};

export default ChitFundPendingBorrowersPage;
