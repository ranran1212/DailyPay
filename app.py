from flask import Flask, request, send_file, render_template
import csv
import io
from datetime import datetime

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # アップロードされた入力CSVファイルを読み込む
        input_csv = request.files['input_csv']
        input_csv_data = input_csv.read().decode('utf-8')
        input_csv_io = io.StringIO(input_csv_data)
        reader = csv.DictReader(input_csv_io)

        # WithholdingTax.csvを読み込む
        with open('WithholdingTax.csv', 'r', encoding='utf-8') as f:
            withholding_reader = csv.DictReader(f)
            withholding_table = []
            for row in withholding_reader:
                row['日給上限（以上）'] = float(row['日給上限（以上）'].replace(',', ''))
                row['日給下限（未満）'] = float(row['日給下限（未満）'].replace(',', ''))
                row['源泉徴収額'] = float(row['源泉徴収額'].replace(',', ''))
                withholding_table.append(row)

        # 出力CSV
        output_csv_io = io.StringIO()
        fieldnames = ['名前', '振込金額', '基本賃金', '交通費', 'インセンティブ', '源泉徴収額']
        writer = csv.DictWriter(output_csv_io, fieldnames=fieldnames)
        writer.writeheader()

        for input_row in reader:
            name = input_row['名前']
            basic_wage = float(input_row['基本賃金'].replace(',', ''))
            transport = float(input_row['交通費'].replace(',', ''))
            incentive = float(input_row['インセンティブ'].replace(',', ''))
            daily_wage = basic_wage + transport + incentive

            # 源泉徴収額を参照
            withholding_tax = 0
            for row in withholding_table:
                lower = row['日給上限（以上）']
                upper = row['日給下限（未満）']
                tax = row['源泉徴収額']
                if lower <= daily_wage < upper:
                    withholding_tax = tax
                    break

            transfer_amount = daily_wage - withholding_tax

            # 数値を整数に変換
            basic_wage_int = int(basic_wage)
            transport_int = int(transport)
            incentive_int = int(incentive)
            daily_wage_int = int(daily_wage)
            withholding_tax_int = int(withholding_tax)
            transfer_amount_int = int(transfer_amount)

            output_row = {
                '名前': name,
                '振込金額': transfer_amount_int,
                '基本賃金': basic_wage_int,
                '交通費': transport_int,
                'インセンティブ': incentive_int,
                '源泉徴収額': withholding_tax_int
            }
            writer.writerow(output_row)

        output_csv_io.seek(0)
        return send_file(
            io.BytesIO(output_csv_io.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'output_{datetime.now().strftime("%Y%m%d%H%M%S")}_日払申請振込額.csv'
        )
    else:
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)
