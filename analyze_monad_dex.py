#!/usr/bin/env python3
"""
Monad DEX交易数据完整分析
基于抓取到的数据完成所有要求的统计分析
"""

import psycopg2
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv

def connect_db():
    """连接数据库"""
    return psycopg2.connect(
        host="localhost",
        database="hemera_indexer",
        user="devuser",
        password="hemera123"
    )

def basic_statistics():
    """基础统计分析"""
    print("=" * 80)
    print("📊 MONAD DEX 交易数据分析报告")
    print("=" * 80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    print("\n🔢 1. 总交易笔数（Swap 数量）")
    print("-" * 50)
    cursor.execute("SELECT COUNT(*) FROM monad_dex_swap_events;")
    total_swaps = cursor.fetchone()[0]
    print(f"总交易笔数: {total_swaps:,} 笔")
    
    print("\n💰 2. 总交易金额（按 Token 分类）")
    print("-" * 50)
    cursor.execute("""
        SELECT 
            SUM(token0_amount_in + token0_amount_out) as total_token0_volume,
            SUM(token1_amount_in + token1_amount_out) as total_token1_volume,
            AVG(token0_amount_in + token0_amount_out) as avg_token0_per_trade,
            AVG(token1_amount_in + token1_amount_out) as avg_token1_per_trade
        FROM monad_dex_swap_events;
    """)
    volume_stats = cursor.fetchone()
    
    # 转换为易读格式
    token0_total = float(volume_stats[0]) / 1e18  # 假设18位小数
    token1_total = float(volume_stats[1]) / 1e6   # 假设6位小数 (USDC)
    token0_avg = float(volume_stats[2]) / 1e18
    token1_avg = float(volume_stats[3]) / 1e6
    
    print(f"MON (Token0) 总交易量: {token0_total:,.2f} MON")
    print(f"USDC (Token1) 总交易量: {token1_total:,.2f} USDC")
    print(f"平均每笔 MON 交易量: {token0_avg:.4f} MON")
    print(f"平均每笔 USDC 交易量: {token1_avg:.2f} USDC")
    
    # 估算USD等价值 (假设 MON = $0.10, 实际需要价格feed)
    estimated_mon_price = 0.10
    estimated_usd_volume = (token0_total * estimated_mon_price) + token1_total
    print(f"估算总USD交易量: ${estimated_usd_volume:,.2f} (假设MON=${estimated_mon_price})")
    
    print("\n👥 3. 涉及的独立交易者地址数（活跃用户）")
    print("-" * 50)
    cursor.execute("SELECT COUNT(DISTINCT trader_address) FROM monad_dex_swap_events;")
    unique_traders = cursor.fetchone()[0]
    print(f"独立交易者地址数: {unique_traders:,} 个")
    print(f"平均每个地址交易次数: {total_swaps/unique_traders:.2f} 次")
    
    # 时间范围信息
    cursor.execute("""
        SELECT 
            MIN(block_timestamp) as earliest,
            MAX(block_timestamp) as latest,
            EXTRACT(EPOCH FROM (MAX(block_timestamp) - MIN(block_timestamp)))/3600 as duration_hours
        FROM monad_dex_swap_events;
    """)
    time_info = cursor.fetchone()
    print(f"\n⏰ 数据时间范围:")
    print(f"开始时间: {time_info[0]}")
    print(f"结束时间: {time_info[1]}")
    print(f"持续时间: {time_info[2]:.2f} 小时")
    
    conn.close()
    return {
        'total_swaps': total_swaps,
        'unique_traders': unique_traders,
        'token0_volume': token0_total,
        'token1_volume': token1_total,
        'estimated_usd_volume': estimated_usd_volume
    }

def time_dimension_analysis():
    """时间维度分析"""
    print("\n" + "=" * 80)
    print("📈 4. 时间维度分析")
    print("=" * 80)
    
    conn = connect_db()
    
    # 每小时交易数据
    print("\n🕐 每小时交易笔数分析")
    print("-" * 50)
    hourly_query = """
        SELECT 
            DATE_TRUNC('hour', block_timestamp) as hour,
            COUNT(*) as swap_count,
            COUNT(DISTINCT trader_address) as unique_traders,
            SUM(token0_amount_in + token0_amount_out)/1e18 as token0_volume,
            SUM(token1_amount_in + token1_amount_out)/1e6 as token1_volume
        FROM monad_dex_swap_events
        GROUP BY DATE_TRUNC('hour', block_timestamp)
        ORDER BY hour;
    """
    
    df_hourly = pd.read_sql(hourly_query, conn)
    print(f"数据覆盖 {len(df_hourly)} 个小时")
    print("\n每小时交易数据预览:")
    print(df_hourly.head(10).to_string(index=False))
    
    # 导出每小时CSV
    df_hourly.to_csv('monad_hourly_trades.csv', index=False)
    print(f"\n📁 每小时数据已导出: monad_hourly_trades.csv")
    
    # 每天交易数据（如果数据跨天）
    daily_query = """
        SELECT 
            DATE_TRUNC('day', block_timestamp) as day,
            COUNT(*) as swap_count,
            COUNT(DISTINCT trader_address) as unique_traders,
            SUM(token0_amount_in + token0_amount_out)/1e18 as token0_volume,
            SUM(token1_amount_in + token1_amount_out)/1e6 as token1_volume,
            MIN(block_timestamp) as first_trade,
            MAX(block_timestamp) as last_trade
        FROM monad_dex_swap_events
        GROUP BY DATE_TRUNC('day', block_timestamp)
        ORDER BY day;
    """
    
    df_daily = pd.read_sql(daily_query, conn)
    
    if len(df_daily) > 1:
        print(f"\n📅 每日交易数据 (共{len(df_daily)}天):")
        print("-" * 50)
        print(df_daily.to_string(index=False))
        df_daily.to_csv('monad_daily_trades.csv', index=False)
        print(f"\n📁 每日数据已导出: monad_daily_trades.csv")
    else:
        print(f"\n📅 数据仅覆盖单日，无需每日分析")
    
    # 生成简化的折线图数据（CSV格式）
    print(f"\n📊 折线图数据生成:")
    print("-" * 50)
    
    # 创建时间序列数据用于绘图
    chart_data = []
    for _, row in df_hourly.iterrows():
        chart_data.append({
            'time': row['hour'].strftime('%Y-%m-%d %H:%M'),
            'swap_count': row['swap_count'],
            'unique_traders': row['unique_traders'],
            'token0_volume': round(row['token0_volume'], 4),
            'token1_volume': round(row['token1_volume'], 2)
        })
    
    # 保存图表数据
    with open('monad_chart_data.csv', 'w', newline='', encoding='utf-8') as f:
        if chart_data:
            writer = csv.DictWriter(f, fieldnames=chart_data[0].keys())
            writer.writeheader()
            writer.writerows(chart_data)
    
    print("📁 折线图数据已导出: monad_chart_data.csv")
    print("   - time: 时间点")
    print("   - swap_count: 每小时交易数")
    print("   - unique_traders: 每小时活跃交易者")
    print("   - token0_volume: 每小时MON交易量")
    print("   - token1_volume: 每小时USDC交易量")
    
    conn.close()

def top_active_addresses():
    """最活跃地址分析（加分项）"""
    print("\n" + "=" * 80)
    print("🏆 5. 最活跃地址（按交易次数排序前5）")
    print("=" * 80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            trader_address,
            COUNT(*) as swap_count,
            SUM(token0_amount_in + token0_amount_out)/1e18 as total_token0_volume,
            SUM(token1_amount_in + token1_amount_out)/1e6 as total_token1_volume,
            MIN(block_timestamp) as first_trade,
            MAX(block_timestamp) as last_trade,
            COUNT(DISTINCT pool_address) as pools_used,
            AVG(gas_used) as avg_gas_used
        FROM monad_dex_swap_events
        GROUP BY trader_address
        ORDER BY swap_count DESC
        LIMIT 5;
    """)
    
    top_traders = cursor.fetchall()
    
    print("🥇 TOP 5 最活跃交易者:")
    print("-" * 70)
    
    for i, trader in enumerate(top_traders, 1):
        print(f"\n{i}. 地址: {trader[0][:8]}...{trader[0][-6:]}")
        print(f"   📊 交易次数: {trader[1]:,} 次")
        print(f"   💰 MON总交易量: {trader[2]:,.4f} MON")
        print(f"   💵 USDC总交易量: {trader[3]:,.2f} USDC")
        print(f"   🕐 首次交易: {trader[4]}")
        print(f"   🕐 最后交易: {trader[5]}")
        print(f"   🏊 使用池数: {trader[6]} 个")
        print(f"   ⛽ 平均Gas: {trader[7]:,.0f}")
    
    conn.close()

def largest_trades():
    """最大交易分析（加分项）"""
    print("\n" + "=" * 80)
    print("💎 6. 最大一笔交易（按金额）")
    print("=" * 80)
    
    conn = connect_db()
    cursor = conn.cursor()
    
    # 按MON金额最大的交易
    print("\n🔥 按MON金额最大的交易:")
    print("-" * 50)
    cursor.execute("""
        SELECT 
            transaction_hash,
            block_number,
            block_timestamp,
            trader_address,
            pool_address,
            (token0_amount_in + token0_amount_out)/1e18 as token0_volume,
            (token1_amount_in + token1_amount_out)/1e6 as token1_volume,
            token_in,
            token_out,
            gas_used,
            gas_price/1e9 as gas_price_gwei
        FROM monad_dex_swap_events
        ORDER BY (token0_amount_in + token0_amount_out) DESC
        LIMIT 1;
    """)
    
    largest_mon = cursor.fetchone()
    if largest_mon:
        print(f"交易哈希: {largest_mon[0][:10]}...{largest_mon[0][-8:]}")
        print(f"区块号: {largest_mon[1]:,}")
        print(f"时间: {largest_mon[2]}")
        print(f"交易者: {largest_mon[3][:8]}...{largest_mon[3][-6:]}")
        print(f"池地址: {largest_mon[4][:8]}...{largest_mon[4][-6:]}")
        print(f"💰 MON金额: {largest_mon[5]:,.4f} MON")
        print(f"💵 USDC金额: {largest_mon[6]:,.2f} USDC")
        print(f"交易对: {largest_mon[7]} → {largest_mon[8]}")
        print(f"Gas使用: {largest_mon[9]:,}")
        print(f"Gas价格: {largest_mon[10]:.2f} Gwei")
    
    # 按USDC金额最大的交易
    print("\n💵 按USDC金额最大的交易:")
    print("-" * 50)
    cursor.execute("""
        SELECT 
            transaction_hash,
            block_number,
            block_timestamp,
            trader_address,
            (token0_amount_in + token0_amount_out)/1e18 as token0_volume,
            (token1_amount_in + token1_amount_out)/1e6 as token1_volume,
            token_in,
            token_out,
            gas_used,
            gas_price/1e9 as gas_price_gwei
        FROM monad_dex_swap_events
        ORDER BY (token1_amount_in + token1_amount_out) DESC
        LIMIT 1;
    """)
    
    largest_usdc = cursor.fetchone()
    if largest_usdc:
        print(f"交易哈希: {largest_usdc[0][:10]}...{largest_usdc[0][-8:]}")
        print(f"区块号: {largest_usdc[1]:,}")
        print(f"时间: {largest_usdc[2]}")
        print(f"交易者: {largest_usdc[3][:8]}...{largest_usdc[3][-6:]}")
        print(f"💰 MON金额: {largest_usdc[4]:,.4f} MON")
        print(f"💵 USDC金额: {largest_usdc[5]:,.2f} USDC")
        print(f"交易对: {largest_usdc[6]} → {largest_usdc[7]}")
        print(f"Gas使用: {largest_usdc[8]:,}")
        print(f"Gas价格: {largest_usdc[9]:.2f} Gwei")
    
    conn.close()

def export_full_data():
    """导出完整数据"""
    print("\n" + "=" * 80)
    print("📋 7. 导出完整数据")
    print("=" * 80)
    
    conn = connect_db()
    
    # 导出所有交易数据
    full_query = """
        SELECT 
            transaction_hash,
            block_number,
            block_timestamp,
            pool_address,
            trader_address,
            to_address,
            token0_amount_in/1e18 as token0_amount_in_formatted,
            token1_amount_in/1e6 as token1_amount_in_formatted,
            token0_amount_out/1e18 as token0_amount_out_formatted,
            token1_amount_out/1e6 as token1_amount_out_formatted,
            token_in,
            token_out,
            event_type,
            gas_used,
            gas_price/1e9 as gas_price_gwei,
            create_time
        FROM monad_dex_swap_events
        ORDER BY block_timestamp DESC;
    """
    
    df_full = pd.read_sql(full_query, conn)
    df_full.to_csv('monad_dex_complete_data.csv', index=False)
    
    print(f"📁 完整数据已导出: monad_dex_complete_data.csv")
    print(f"   总记录数: {len(df_full):,}")
    print(f"   字段数: {len(df_full.columns)}")
    
    conn.close()

def generate_summary():
    """生成分析摘要"""
    print("\n" + "=" * 80)
    print("📄 8. 分析摘要")
    print("=" * 80)
    
    stats = basic_statistics()
    
    summary = f"""
MONAD DEX 交易数据分析摘要
========================

数据概况:
- 总交易笔数: {stats['total_swaps']:,} 笔
- 独立交易者: {stats['unique_traders']:,} 个
- MON总交易量: {stats['token0_volume']:,.2f} MON
- USDC总交易量: {stats['token1_volume']:,.2f} USDC
- 估算USD交易量: ${stats['estimated_usd_volume']:,.2f}

生成的文件:
- monad_hourly_trades.csv: 每小时交易统计
- monad_daily_trades.csv: 每日交易统计（如适用）
- monad_chart_data.csv: 折线图数据
- monad_dex_complete_data.csv: 完整交易数据

分析完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
    
    with open('monad_analysis_summary.txt', 'w', encoding='utf-8') as f:
        f.write(summary)
    
    print(summary)
    print("📁 分析摘要已保存: monad_analysis_summary.txt")

def main():
    """主函数"""
    try:
        print("🚀 开始 MONAD DEX 数据分析...")
        
        # 执行所有分析
        basic_statistics()
        time_dimension_analysis()
        top_active_addresses()
        largest_trades()
        export_full_data()
        generate_summary()
        
        print("\n" + "=" * 80)
        print("✅ 所有分析完成！")
        print("=" * 80)
        print("📂 生成的文件列表:")
        print("   - monad_hourly_trades.csv (每小时交易数据)")
        print("   - monad_daily_trades.csv (每日交易数据)")
        print("   - monad_chart_data.csv (折线图数据)")
        print("   - monad_dex_complete_data.csv (完整交易数据)")
        print("   - monad_analysis_summary.txt (分析摘要)")
        print("\n💡 您可以使用这些CSV文件在Excel或其他工具中创建图表")
        
    except Exception as e:
        print(f"❌ 分析过程中出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 