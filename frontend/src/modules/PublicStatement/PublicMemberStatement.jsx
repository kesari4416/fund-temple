import React, { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import axios from "axios";
import styled from "styled-components";

const API_BASE =
  import.meta.env.VITE_BACKEND_URL ||
  import.meta.env.REACT_APP_BACKEND_URL ||
  "";

const Wrap = styled.div`
  min-height: 100vh;
  background: #f8fafc;
  color: #0f172a;
  padding: 24px 16px;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
`;

const Card = styled.div`
  background: #ffffff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.06);
  max-width: 720px;
  margin: 0 auto 16px auto;
`;

const Row = styled.div`
  display: flex;
  justify-content: space-between;
  gap: 8px;
  border-bottom: 1px solid #e2e8f0;
  padding: 8px 0;
  font-size: 14px;
  &:last-child { border-bottom: 0; }
`;

const Chip = styled.span`
  display: inline-block;
  padding: 2px 10px;
  background: #ecfdf5;
  color: #065f46;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
`;

const Title = styled.h1`
  font-size: 20px;
  margin: 0 0 4px 0;
  color: #0f5132;
`;

const Muted = styled.p`
  margin: 0;
  color: #64748b;
  font-size: 13px;
`;

const fmt = (n) => `\u20B9 ${Number(n || 0).toFixed(2)}`;

const PublicMemberStatement = () => {
  const { token } = useParams();
  const [state, setState] = useState({ loading: true, error: null, data: null });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const url = `${API_BASE}/api/collection/public/member_statement/${token}/`;
        const { data } = await axios.get(url);
        if (!cancelled) setState({ loading: false, error: null, data });
      } catch (err) {
        if (!cancelled)
          setState({
            loading: false,
            error:
              err?.response?.data?.detail ||
              "This statement link is invalid or has expired.",
            data: null,
          });
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [token]);

  if (state.loading)
    return (
      <Wrap data-testid="statement-loading">
        <Card>Loading your statement…</Card>
      </Wrap>
    );

  if (state.error)
    return (
      <Wrap data-testid="statement-error">
        <Card>
          <Title>Statement unavailable</Title>
          <Muted>{state.error}</Muted>
        </Card>
      </Wrap>
    );

  const { member, period, collections, totals, pending_dues } = state.data;

  return (
    <Wrap data-testid="statement-root">
      <Card>
        <Title data-testid="statement-member-name">
          {[member.name, member.last_name].filter(Boolean).join(" ")}
        </Title>
        <Muted>
          Member No: {member.member_no || "-"} · Mobile:{" "}
          {member.mobile || "-"}
        </Muted>
        <Muted style={{ marginTop: 6 }}>
          Statement period: {period.from} to {period.to}
        </Muted>
      </Card>

      <Card>
        <Row>
          <strong>Total collections received (1 year)</strong>
          <Chip data-testid="statement-total-amount">{fmt(totals.amount)}</Chip>
        </Row>
        <Row>
          <span>Number of payments</span>
          <span data-testid="statement-total-count">{totals.count}</span>
        </Row>
      </Card>

      <Card>
        <Title style={{ fontSize: 16 }}>Payments (most recent first)</Title>
        {collections.length === 0 ? (
          <Muted style={{ marginTop: 12 }} data-testid="statement-no-payments">
            No payments recorded in the last 12 months.
          </Muted>
        ) : (
          <div style={{ marginTop: 8 }} data-testid="statement-payments-list">
            {collections.map((c) => (
              <Row key={c.id}>
                <div>
                  <div style={{ fontWeight: 600 }}>{c.category || "—"}</div>
                  <Muted>
                    {c.date} · {c.payment_mode || "-"}
                    {c.collection_no ? ` · #${c.collection_no}` : ""}
                  </Muted>
                </div>
                <div style={{ textAlign: "right" }}>
                  <div>{fmt(c.amount)}</div>
                  <Muted>Running: {fmt(c.running_total)}</Muted>
                </div>
              </Row>
            ))}
          </div>
        )}
      </Card>

      <Card>
        <Title style={{ fontSize: 16 }}>Pending dues</Title>
        {Object.keys(pending_dues).filter((k) => k !== "Total").length === 0 ? (
          <Muted style={{ marginTop: 12 }} data-testid="statement-no-pending">
            No pending dues.
          </Muted>
        ) : (
          <div style={{ marginTop: 8 }} data-testid="statement-pending-list">
            {Object.entries(pending_dues).map(([k, v]) =>
              k === "Total" ? null : (
                <Row key={k}>
                  <span>{k}</span>
                  <span>{fmt(v)}</span>
                </Row>
              )
            )}
            <Row>
              <strong>Total pending</strong>
              <Chip
                data-testid="statement-pending-total"
                style={{ background: "#fef3c7", color: "#92400e" }}
              >
                {fmt(pending_dues.Total)}
              </Chip>
            </Row>
          </div>
        )}
      </Card>
    </Wrap>
  );
};

export default PublicMemberStatement;
