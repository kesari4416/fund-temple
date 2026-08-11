import { CustomStandardTable } from "@components/form/CustomStandardTable"
import { Fragment } from "react"

export const ChitfundInvesView = ({ datas }) => {
    const ColumnTable = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Income Name',
            dataIndex: 'name'
        },
        {
            title: 'Amount',
            dataIndex: 'amount'
        },
    ]
    return (
        <Fragment>
            {datas?.map((item, index) => (
                <div key={index}>
                    <h4 style={{color:'#990000'}}>{item?.chitfund_name}</h4>
                    <CustomStandardTable columns={ColumnTable} data={item?.details} pagination={false} />
                </div>
            ))}
        </Fragment>
    )
}

export const ChitfundInterestGivenView = ({ datas }) => {

    const ValuesData = datas?.Chit_fund_Interest_Given?.details || []

    const ColumnTable = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Name',
            dataIndex: 'name'
        },
        {
            title: 'Amount',
            dataIndex: 'amount'
        },
    ]

    return (
        <div>
            <CustomStandardTable columns={ColumnTable} data={ValuesData} pagination={false} />
        </div>
    )
}

export const CFProfitDistributionView = ({ datas }) => {

    const ValuesData = datas?.Chit_fund_Profit_Distribution?.details || []

    const ColumnTable = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Name',
            dataIndex: 'name'
        },
        {
            title: 'Amount',
            dataIndex: 'amount'
        },
    ]

    return (
        <div>
            <CustomStandardTable columns={ColumnTable} data={ValuesData} pagination={false} />
        </div>
    )
}

// Feb 2026 owner rule: line-item breakdown for the "Chit Fund Expense"
// entry on the Debit column of the Chit-Fund Balance Sheet. Uses the
// same column layout as Interest Given / Profit Distribution so the
// section reads consistently. Backend payload (dic1['Chit_Fund_Expense'])
// already includes `chit_fund_name`, `expense_name`, and `amount` for
// each row.
export const ChitFundExpenseView = ({ datas }) => {

    const ValuesData = datas?.Chit_Fund_Expense?.details || []

    const ColumnTable = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Chit Fund',
            dataIndex: 'chit_fund_name',
            render: (val) => val || '-',
        },
        {
            title: 'Expense Name',
            dataIndex: 'expense_name'
        },
        {
            title: 'Amount',
            dataIndex: 'amount'
        },
    ]

    return (
        <div>
            <CustomStandardTable columns={ColumnTable} data={ValuesData} pagination={false} />
        </div>
    )
}

export const FromCollectionView = ({ datas }) => {

    const ValuesData = datas?.From_Collection?.details || []

    const ColumnTable = [
        {
            title: 'Sl No',
            render: (value, item, index) => index + 1,
        },
        {
            title: 'Name',
            dataIndex: 'name'
        },
        {
            title: 'Amount',
            dataIndex: 'amount'
        },
    ]

    return (
        <div>
            <CustomStandardTable columns={ColumnTable} data={ValuesData} pagination={false} />
        </div>
    )
}