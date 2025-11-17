"""
AI异常检测服务
Version: 1.0
Author: Claude协作开发
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import List, Dict, Any, Optional, Tuple
import statistics
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from models.daily_report import DailyReport
from models.ad_account import AdAccount


class AIAnomalyDetectionService:
    """AI异常检测服务"""

    def __init__(self, db: Session):
        self.db = db

    def detect_performance_anomalies(self, performance_data: List[Dict]) -> Dict[str, Any]:
        """检测绩效异常"""
        if not performance_data:
            return {
                "has_anomalies": False,
                "anomalies": [],
                "analysis_summary": {
                    "total_data_points": 0,
                    "anomaly_count": 0,
                    "message": "数据不足，无法进行异常检测"
                }
            }

        anomalies = []

        # 检测消耗异常
        spends = [float(d.get("spend", 0)) for d in performance_data]
        if len(spends) >= 3:
            spend_anomalies = self._detect_spend_anomalies(spends, performance_data)
            anomalies.extend(spend_anomalies)

        # 检测点击率异常
        ctrs = []
        for d in performance_data:
            impressions = d.get("impressions", 0)
            clicks = d.get("clicks", 0)
            if impressions > 0:
                ctr = (clicks / impressions) * 100
                ctrs.append(ctr)

        if len(ctrs) >= 3:
            ctr_anomalies = self._detect_ctr_anomalies(ctrs, performance_data)
            anomalies.extend(ctr_anomalies)

        # 检测转化率异常
        cvrs = []
        for d in performance_data:
            clicks = d.get("clicks", 0)
            conversions = d.get("conversions", 0)
            if clicks > 0:
                cvr = (conversions / clicks) * 100
                cvrs.append(cvr)

        if len(cvrs) >= 3:
            cvr_anomalies = self._detect_cvr_anomalies(cvrs, performance_data)
            anomalies.extend(cvr_anomalies)

        # 检测CPA异常
        cpas = [float(d.get("cpa", 0)) for d in performance_data if d.get("cpa", 0) > 0]
        if len(cpas) >= 3:
            cpa_anomalies = self._detect_cpa_anomalies(cpas, performance_data)
            anomalies.extend(cpa_anomalies)

        # 检测ROAS异常
        roas = [float(d.get("roas", 0)) for d in performance_data if d.get("roas", 0) > 0]
        if len(roas) >= 3:
            roas_anomalies = self._detect_roas_anomalies(roas, performance_data)
            anomalies.extend(roas_anomalies)

        return {
            "has_anomalies": len(anomalies) > 0,
            "anomalies": anomalies,
            "analysis_summary": {
                "total_data_points": len(performance_data),
                "anomaly_count": len(anomalies),
                "checked_metrics": ["spend", "ctr", "cvr", "cpa", "roas"]
            }
        }

    def _detect_spend_anomalies(self, spends: List[float], performance_data: List[Dict]) -> List[Dict]:
        """检测消耗异常"""
        anomalies = []
        if len(spends) < 3:
            return anomalies

        threshold = 2.0  # Z-score阈值
        window = min(7, len(spends) // 2)

        for i in range(window, len(spends)):
            recent_spends = spends[i-window:i]
            mean_spend = statistics.mean(recent_spends)
            std_spend = statistics.stdev(recent_spends) if len(recent_spends) > 1 else 0

            if std_spend > 0:
                z_score = (spends[i] - mean_spend) / std_spend
                if abs(z_score) > threshold:
                    anomaly_type = "spend_spike" if z_score > 0 else "spend_drop"
                    severity = min(abs(z_score) / threshold, 5.0)

                    anomalies.append({
                        "date": performance_data[i].get("date"),
                        "metric": "spend",
                        "value": spends[i],
                        "expected_range": [mean_spend - 2*std_spend, mean_spend + 2*std_spend],
                        "anomaly_type": anomaly_type,
                        "severity": "high" if severity > 3 else "medium" if severity > 2 else "low",
                        "z_score": z_score,
                        "description": f"消耗异常{('激增' if z_score > 0 else '骤降')}: {spends[i]:.2f} (预期: {mean_spend:.2f})"
                    })

        return anomalies

    def _detect_ctr_anomalies(self, ctrs: List[float], performance_data: List[Dict]) -> List[Dict]:
        """检测点击率异常"""
        anomalies = []
        if len(ctrs) < 3:
            return anomalies

        threshold = 2.0
        window = min(7, len(ctrs) // 2)

        for i in range(window, len(ctrs)):
            recent_ctrs = ctrs[i-window:i]
            mean_ctr = statistics.mean(recent_ctrs)
            std_ctr = statistics.stdev(recent_ctrs) if len(recent_ctrs) > 1 else 0

            if std_ctr > 0:
                z_score = (ctrs[i] - mean_ctr) / std_ctr
                if abs(z_score) > threshold:
                    anomaly_type = "ctr_spike" if z_score > 0 else "ctr_drop"
                    severity = min(abs(z_score) / threshold, 5.0)

                    anomalies.append({
                        "date": performance_data[i].get("date"),
                        "metric": "ctr",
                        "value": ctrs[i],
                        "expected_range": [mean_ctr - 2*std_ctr, mean_ctr + 2*std_ctr],
                        "anomaly_type": anomaly_type,
                        "severity": "high" if severity > 3 else "medium" if severity > 2 else "low",
                        "z_score": z_score,
                        "description": f"点击率异常{('激增' if z_score > 0 else '骤降')}: {ctrs[i]:.2f}% (预期: {mean_ctr:.2f}%)"
                    })

        return anomalies

    def _detect_cvr_anomalies(self, cvrs: List[float], performance_data: List[Dict]) -> List[Dict]:
        """检测转化率异常"""
        anomalies = []
        if len(cvrs) < 3:
            return anomalies

        threshold = 2.0
        window = min(7, len(cvrs) // 2)

        for i in range(window, len(cvrs)):
            recent_cvrs = cvrs[i-window:i]
            mean_cvr = statistics.mean(recent_cvrs)
            std_cvr = statistics.stdev(recent_cvrs) if len(recent_cvrs) > 1 else 0

            if std_cvr > 0:
                z_score = (cvrs[i] - mean_cvr) / std_cvr
                if abs(z_score) > threshold:
                    anomaly_type = "cvr_spike" if z_score > 0 else "cvr_drop"
                    severity = min(abs(z_score) / threshold, 5.0)

                    anomalies.append({
                        "date": performance_data[i].get("date"),
                        "metric": "cvr",
                        "value": cvrs[i],
                        "expected_range": [mean_cvr - 2*std_cvr, mean_cvr + 2*std_cvr],
                        "anomaly_type": anomaly_type,
                        "severity": "high" if severity > 3 else "medium" if severity > 2 else "low",
                        "z_score": z_score,
                        "description": f"转化率异常{('激增' if z_score > 0 else '骤降')}: {cvrs[i]:.2f}% (预期: {mean_cvr:.2f}%)"
                    })

        return anomalies

    def _detect_cpa_anomalies(self, cpas: List[float], performance_data: List[Dict]) -> List[Dict]:
        """检测CPA异常"""
        anomalies = []
        if len(cpas) < 3:
            return anomalies

        threshold = 2.0
        window = min(7, len(cpas) // 2)

        for i in range(window, len(cpas)):
            recent_cpas = cpas[i-window:i]
            mean_cpa = statistics.mean(recent_cpas)
            std_cpa = statistics.stdev(recent_cpas) if len(recent_cpas) > 1 else 0

            if std_cpa > 0:
                z_score = (cpas[i] - mean_cpa) / std_cpa
                if abs(z_score) > threshold:
                    anomaly_type = "cpa_spike" if z_score > 0 else "cpa_drop"
                    severity = min(abs(z_score) / threshold, 5.0)

                    anomalies.append({
                        "date": performance_data[i].get("date"),
                        "metric": "cpa",
                        "value": cpas[i],
                        "expected_range": [mean_cpa - 2*std_cpa, mean_cpa + 2*std_cpa],
                        "anomaly_type": anomaly_type,
                        "severity": "high" if severity > 3 else "medium" if severity > 2 else "low",
                        "z_score": z_score,
                        "description": f"CPA异常{('激增' if z_score > 0 else '骤降')}: {cpas[i]:.2f} (预期: {mean_cpa:.2f})"
                    })

        return anomalies

    def _detect_roas_anomalies(self, roas: List[float], performance_data: List[Dict]) -> List[Dict]:
        """检测ROAS异常"""
        anomalies = []
        if len(roas) < 3:
            return anomalies

        threshold = 2.0
        window = min(7, len(roas) // 2)

        for i in range(window, len(roas)):
            recent_roas = roas[i-window:i]
            mean_roas = statistics.mean(recent_roas)
            std_roas = statistics.stdev(recent_roas) if len(recent_roas) > 1 else 0

            if std_roas > 0:
                z_score = (roas[i] - mean_roas) / std_roas
                if abs(z_score) > threshold:
                    anomaly_type = "roas_spike" if z_score > 0 else "roas_drop"
                    severity = min(abs(z_score) / threshold, 5.0)

                    anomalies.append({
                        "date": performance_data[i].get("date"),
                        "metric": "roas",
                        "value": roas[i],
                        "expected_range": [mean_roas - 2*std_roas, mean_roas + 2*std_roas],
                        "anomaly_type": anomaly_type,
                        "severity": "high" if severity > 3 else "medium" if severity > 2 else "low",
                        "z_score": z_score,
                        "description": f"ROAS异常{('激增' if z_score > 0 else '骤降')}: {roas[i]:.2f} (预期: {mean_roas:.2f})"
                    })

        return anomalies

    def assess_account_lifetime_risk(self, account_data: Dict, performance_data: List[Dict]) -> Dict[str, Any]:
        """评估账户寿命风险"""
        risk_score = 0
        risk_factors = []

        # 基于账户年龄的风险
        if "created_at" in account_data:
            account_age = (datetime.now() - account_data["created_at"]).days
            if account_age < 7:
                risk_score += 20
                risk_factors.append({
                    "type": "new_account",
                    "description": "账户创建时间较短，稳定性未知",
                    "impact": "medium"
                })
            elif account_age > 180:
                risk_score += 10
                risk_factors.append({
                    "type": "old_account",
                    "description": "账户运行时间较长，可能面临政策风险",
                    "impact": "low"
                })

        # 基于绩效趋势的风险
        if len(performance_data) >= 7:
            recent_spends = [float(d.get("spend", 0)) for d in performance_data[-7:]]
            older_spends = [float(d.get("spend", 0)) for d in performance_data[-14:-7]] if len(performance_data) >= 14 else []

            if older_spends:
                spend_trend = statistics.mean(recent_spends) - statistics.mean(older_spends)
                if spend_trend < -50:  # 消耗显著下降
                    risk_score += 30
                    risk_factors.append({
                        "type": "spend_decline",
                        "description": "近期消耗显著下降",
                        "impact": "high"
                    })

            # 检查绩效异常
            anomaly_result = self.detect_performance_anomalies(performance_data)
            if anomaly_result["has_anomalies"]:
                high_severity_anomalies = [a for a in anomaly_result["anomalies"] if a.get("severity") == "high"]
                risk_score += len(high_severity_anomalies) * 10
                risk_factors.append({
                    "type": "performance_anomalies",
                    "description": f"检测到{len(high_severity_anomalies)}个高严重度绩效异常",
                    "impact": "high"
                })

        # 基于账户状态的风险
        if account_data.get("status") == "restricted":
            risk_score += 50
            risk_factors.append({
                "type": "account_restricted",
                "description": "账户状态受限",
                "impact": "critical"
            })
        elif account_data.get("status") == "warning":
            risk_score += 25
            risk_factors.append({
                "type": "account_warning",
                "description": "账户状态警告",
                "impact": "high"
            })

        # 确定风险等级
        if risk_score >= 70:
            risk_level = "critical"
        elif risk_score >= 50:
            risk_level = "high"
        elif risk_score >= 30:
            risk_level = "medium"
        else:
            risk_level = "low"

        # 预测剩余寿命（天）
        if risk_level == "critical":
            predicted_lifetime = 7
        elif risk_level == "high":
            predicted_lifetime = 30
        elif risk_level == "medium":
            predicted_lifetime = 90
        else:
            predicted_lifetime = 180

        return {
            "account_id": account_data.get("id"),
            "risk_score": min(risk_score, 100),
            "risk_level": risk_level,
            "lifetime_prediction_days": predicted_lifetime,
            "risk_factors": risk_factors,
            "recommendations": self._generate_risk_recommendations(risk_level, risk_factors),
            "assessment_time": datetime.now().isoformat()
        }

    def _generate_risk_recommendations(self, risk_level: str, risk_factors: List[Dict]) -> List[Dict]:
        """生成风险建议"""
        recommendations = []

        if risk_level in ["critical", "high"]:
            recommendations.append({
                "type": "immediate_action",
                "priority": "urgent",
                "description": "立即检查账户政策和合规性",
                "action": "review_account_compliance"
            })

        for factor in risk_factors:
            if factor["type"] == "spend_decline":
                recommendations.append({
                    "type": "performance_optimization",
                    "priority": "high",
                    "description": "优化广告素材和目标定位",
                    "action": "optimize_campaigns"
                })
            elif factor["type"] == "performance_anomalies":
                recommendations.append({
                    "type": "monitoring",
                    "priority": "medium",
                    "description": "加强绩效监控和频率",
                    "action": "increase_monitoring"
                })
            elif factor["type"] == "new_account":
                recommendations.append({
                    "type": "warm_up",
                    "priority": "medium",
                    "description": "逐步增加投放预算，避免激进行为",
                    "action": "gradual_scaling"
                })

        return recommendations

    def get_account_insights(self, account_data: Dict, performance_data: List[Dict]) -> Dict[str, Any]:
        """获取账户洞察"""
        # 基础统计
        total_spend = sum(float(d.get("spend", 0)) for d in performance_data)
        total_conversions = sum(d.get("conversions", 0) for d in performance_data)
        total_clicks = sum(d.get("clicks", 0) for d in performance_data)
        total_impressions = sum(d.get("impressions", 0) for d in performance_data)

        avg_cpa = total_spend / total_conversions if total_conversions > 0 else 0
        avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
        avg_cvr = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0
        roas = (total_conversions * 50) / total_spend if total_spend > 0 else 0  # 假设每次转化价值50

        # 趋势分析
        trends = self._analyze_trends(performance_data)

        # 异常检测
        anomaly_result = self.detect_performance_anomalies(performance_data)

        # 风险评估
        risk_assessment = self.assess_account_lifetime_risk(account_data, performance_data)

        # 生成建议
        recommendations = self._generate_insights_recommendations(
            total_spend, avg_cpa, avg_ctr, anomaly_result, risk_assessment
        )

        return {
            "account_id": account_data.get("id"),
            "account_name": account_data.get("name"),
            "performance_summary": {
                "total_spend": round(total_spend, 2),
                "total_conversions": total_conversions,
                "total_clicks": total_clicks,
                "total_impressions": total_impressions,
                "avg_cpa": round(avg_cpa, 2),
                "avg_ctr": round(avg_ctr, 2),
                "avg_cvr": round(avg_cvr, 2),
                "roas": round(roas, 2)
            },
            "trends": trends,
            "anomalies": anomaly_result,
            "risk_assessment": risk_assessment,
            "recommendations": recommendations,
            "generated_at": datetime.now().isoformat()
        }

    def _analyze_trends(self, performance_data: List[Dict]) -> Dict[str, Any]:
        """分析趋势"""
        if len(performance_data) < 7:
            return {"message": "数据不足，无法分析趋势"}

        recent_data = performance_data[-7:]
        older_data = performance_data[-14:-7] if len(performance_data) >= 14 else performance_data[:-7]

        recent_spend = statistics.mean([float(d.get("spend", 0)) for d in recent_data])
        older_spend = statistics.mean([float(d.get("spend", 0)) for d in older_data])

        spend_trend = ((recent_spend - older_spend) / older_spend * 100) if older_spend > 0 else 0

        recent_ctr = statistics.mean([
            (d.get("clicks", 0) / d.get("impressions", 1) * 100)
            for d in recent_data if d.get("impressions", 0) > 0
        ])

        older_ctr = statistics.mean([
            (d.get("clicks", 0) / d.get("impressions", 1) * 100)
            for d in older_data if d.get("impressions", 0) > 0
        ])

        ctr_trend = ((recent_ctr - older_ctr) / older_ctr * 100) if older_ctr > 0 else 0

        return {
            "spend_trend_percent": round(spend_trend, 2),
            "ctr_trend_percent": round(ctr_trend, 2),
            "trend_period": f"最近{len(recent_data)}天 vs 前{len(older_data)}天",
            "interpretation": self._interpret_trends(spend_trend, ctr_trend)
        }

    def _interpret_trends(self, spend_trend: float, ctr_trend: float) -> str:
        """解读趋势"""
        interpretations = []

        if spend_trend > 20:
            interpretations.append("消耗快速增长")
        elif spend_trend < -20:
            interpretations.append("消耗明显下降")
        else:
            interpretations.append("消耗保持稳定")

        if ctr_trend > 15:
            interpretations.append("点击率提升")
        elif ctr_trend < -15:
            interpretations.append("点击率下降")
        else:
            interpretations.append("点击率稳定")

        return "，".join(interpretations)

    def _generate_insights_recommendations(self, total_spend: float, avg_cpa: float,
                                         avg_ctr: float, anomaly_result: Dict,
                                         risk_assessment: Dict) -> List[Dict]:
        """生成洞察建议"""
        recommendations = []

        # 基于CPA的建议
        if avg_cpa > 100:  # 假设CPA阈值
            recommendations.append({
                "type": "cost_optimization",
                "priority": "high",
                "description": f"CPA较高({avg_cpa:.2f})，建议优化目标定位和出价",
                "potential_impact": "CPA降低20-30%"
            })

        # 基于CTR的建议
        if avg_ctr < 1.0:  # 假设CTR阈值
            recommendations.append({
                "type": "creative_optimization",
                "priority": "medium",
                "description": f"点击率较低({avg_ctr:.2f}%)，建议测试新的广告素材",
                "potential_impact": "CTR提升50-100%"
            })

        # 基于异常的建议
        if anomaly_result["has_anomalies"]:
            recommendations.append({
                "type": "anomaly_investigation",
                "priority": "urgent",
                "description": f"检测到{anomaly_result['analysis_summary']['anomaly_count']}个异常，需要立即调查",
                "potential_impact": "避免进一步损失"
            })

        # 基于风险的建议
        if risk_assessment["risk_level"] in ["high", "critical"]:
            recommendations.append({
                "type": "risk_mitigation",
                "priority": "urgent",
                "description": f"账户风险{risk_assessment['risk_level']}，建议采取风险缓解措施",
                "potential_impact": "延长账户寿命"
            })

        # 基于消耗的建议
        if total_spend < 100:  # 假设最小消耗阈值
            recommendations.append({
                "type": "scale_up",
                "priority": "low",
                "description": "消耗较低，可以适当增加预算测试更多机会",
                "potential_impact": "增加转化量"
            })

        return recommendations

    def batch_anomaly_detection(self, accounts_data: List[Dict]) -> Dict[str, Any]:
        """批量异常检测"""
        results = []
        total_anomalies = 0

        for account_data in accounts_data:
            account_id = account_data.get("id")
            performance_data = account_data.get("performance_data", [])

            anomaly_result = self.detect_performance_anomalies(performance_data)

            results.append({
                "account_id": account_id,
                "account_name": account_data.get("name"),
                "has_anomalies": anomaly_result["has_anomalies"],
                "anomaly_count": anomaly_result["analysis_summary"]["anomaly_count"],
                "anomalies": anomaly_result["anomalies"]
            })

            total_anomalies += anomaly_result["analysis_summary"]["anomaly_count"]

        accounts_with_anomalies = sum(1 for r in results if r["has_anomalies"])

        return {
            "total_accounts": len(accounts_data),
            "accounts_with_anomalies": accounts_with_anomalies,
            "total_anomalies": total_anomalies,
            "anomaly_rate": (accounts_with_anomalies / len(accounts_data) * 100) if accounts_data else 0,
            "anomaly_details": results,
            "analysis_time": datetime.now().isoformat()
        }