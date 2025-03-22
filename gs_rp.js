function main() {
    // **Phần 1: Lấy dữ liệu chiến dịch có phát sinh chi phí**
    var campaignQuery = "SELECT CampaignName, Clicks, Conversions, Cost " +
        "FROM CAMPAIGN_PERFORMANCE_REPORT " +
        "WHERE Impressions > 0 AND Cost > 0 " +
        "DURING TODAY";
    var campaignReport = AdsApp.report(campaignQuery);
    var campaignRows = campaignReport.rows();

    var campaignData = [];
    var totalClicks = 0;
    var totalConversions = 0;
    var totalCost = 0;

    while (campaignRows.hasNext()) {
        var row = campaignRows.next();
        var clicksVal = parseFloat(row["Clicks"].replace(/,/g, ''));
        var convVal = parseFloat(row["Conversions"].replace(/,/g, ''));
        var costVal = Math.round(parseFloat(row["Cost"].replace(/,/g, ''))); // Làm tròn chi phí

        campaignData.push({
            campaignName: row["CampaignName"],
            clicks: clicksVal,
            conversions: convVal,
            cost: costVal
        });

        totalClicks += clicksVal;
        totalConversions += convVal;
        totalCost += costVal;
    }

    // **Phần 2: Lấy dữ liệu từ khóa có CPC cao nhất**
    var keywordQuery = "SELECT CampaignName, AdGroupName, Criteria, Cost, Clicks " +
        "FROM KEYWORDS_PERFORMANCE_REPORT " +
        "WHERE Impressions > 0 AND Clicks > 0 " +
        "DURING TODAY";
    var keywordReport = AdsApp.report(keywordQuery);
    var keywordRows = keywordReport.rows();

    var keywordData = [];

    while (keywordRows.hasNext()) {
        var row = keywordRows.next();
        var costVal = Math.round(parseFloat(row["Cost"].replace(/,/g, ''))); // Làm tròn chi phí
        var clicksVal = parseFloat(row["Clicks"].replace(/,/g, ''));
        var cpc = clicksVal > 0 ? costVal / clicksVal : 0;

        keywordData.push({
            campaignName: row["CampaignName"],
            adGroupName: row["AdGroupName"],
            keywordText: row["Criteria"],
            cpc: cpc
        });
    }

    // Sắp xếp từ khóa theo CPC giảm dần và lấy top 5
    keywordData.sort(function (a, b) {
        return b.cpc - a.cpc;
    });
    var topKeywords = keywordData.slice(0, 5);

    // **Phần 3: Tạo và gửi báo cáo qua webhook nếu có dữ liệu**
    if (campaignData.length > 0 || topKeywords.length > 0) {
        // Tạo các phần tử cho card message
        var now = new Date();
        var formattedTime = now.toLocaleString('vi-VN', {
            timeZone: 'Asia/Ho_Chi_Minh', // đảm bảo sử dụng múi giờ Việt Nam
            year: 'numeric',
            month: '2-digit',
            day: '2-digit',
            hour: '2-digit',
            minute: '2-digit',
            second: '2-digit'
        });

        var reportTitle = "📊 BÁO CÁO QUẢNG CÁO (HÔM NAY - " + formattedTime + ")";


        var cardElements = [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "<font color='blue'>**" + reportTitle + "**"
                }
            },
            {
                "tag": "hr"
            }
        ];

        // Thêm báo cáo top 5 từ khóa có CPC cao nhất
        if (topKeywords.length > 0) {
            cardElements.push(
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "<font color='green'>**🔝 Top 5 từ khóa có CPC cao nhất:**</font>"
                    }
                }
            );

            topKeywords.forEach(function (keyword, index) {
                var keywordStr =
                    "**Top " + (index + 1) + "**\n" +
                    "- **Từ khóa:** " + keyword.keywordText + "\n" +
                    "- **Chiến dịch:** " + keyword.campaignName + "\n" +
                    "- **Nhóm quảng cáo:** " + keyword.adGroupName + "\n" +
                    "- **CPC:** " + keyword.cpc.toFixed(2) + "đ\n";
                cardElements.push(
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": keywordStr
                        }
                    },

                );
            });
        }

        // Thêm báo cáo chiến dịch có phát sinh chi phí
        if (campaignData.length > 0) {
            cardElements.push(
                {
                    "tag": "hr"
                },
                {
                    "tag": "div",
                    "text": {
                        "tag": "lark_md",
                        "content": "<font color='red'>**💸 Tổng chi phí chiến dịch:**</font>"
                    }
                }
            );

            campaignData.forEach(function (item, index) {
                var contentStr =
                    "**Chiến dịch:** " + item.campaignName + "\n" +
                    "- **Lần nhấp:** " + item.clicks.toLocaleString() + "\n" +
                    "- **Lượt chuyển đổi:** " + item.conversions.toLocaleString() + "\n" +
                    "- **Chi phí:** " + item.cost.toLocaleString() + "đ\n";
                cardElements.push(
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": "### Bản ghi " + (index + 1)
                        }
                    },
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": contentStr
                        }
                    }
                );
            });

            // Thêm tổng cuối cùng cho chiến dịch
            var totalStr =
                "<font color='purple'>**TỔNG CUỐI CÙNG (Chiến dịch)**</font>\n" +
                "- **Tổng Lần nhấp:** " + totalClicks.toLocaleString() + "\n" +
                "- **Tổng Lượt chuyển đổi:** " + totalConversions.toLocaleString() + "\n" +
                "- **Tổng Chi phí:** " + totalCost.toLocaleString() + "đ\n";
            cardElements.push({
                "tag": "hr"
            }, {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": totalStr
                }
            });
        }

        // Tạo payload cho card message
        var cardPayload = {
            "msg_type": "interactive",
            "card": {
                "config": {
                    "wide_screen_mode": true
                },
                "elements": cardElements
            }
        };

        // URL webhook của Lark (thay bằng URL thực tế của bạn)
        var webhookUrl = "https://open.larksuite.com/open-apis/bot/v2/hook/992413a8-ee5f-4a62-8742-aca039cf5263";

        // Tùy chọn cho yêu cầu HTTP
        var optionsLark = {
            "method": "post",
            "contentType": "application/json",
            "payload": JSON.stringify(cardPayload)
        };

        // Gửi báo cáo qua webhook
        try {
            var responseLark = UrlFetchApp.fetch(webhookUrl, optionsLark);
            Logger.log("Đã gửi báo cáo thành công: " + responseLark.getContentText());
        } catch (e) {
            Logger.log("Gửi báo cáo thất bại: " + e);
        }
    } else {
        Logger.log("Không có dữ liệu để báo cáo.");
    }
}