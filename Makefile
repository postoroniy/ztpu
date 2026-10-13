# CI and release targets. Direct ZLang commands are documented in README.md.
ZLANGC ?= $(if $(wildcard .venv/bin/zlang),.venv/bin/zlang,zlang)
PYTHON ?= $(if $(wildcard .venv/bin/python),.venv/bin/python,python3)
VERILATOR ?= verilator
IVERILOG ?= iverilog
VVP ?= vvp

PROJECT := zlang.toml
BUILD_DIR := build
PE_SOURCE := src/pe.zhl
PE_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuPeQ16.sv
ARITH_SOURCE := src/arithmetic.zhl
ACTIVATION_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuActivationQ16x4.sv
BAU_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuBiasAccumulateQ16x4.sv
RQ8_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuAccRequant8.sv
RQ16_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuAccRequant16.sv
RQ32_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuAccRequant32.sv
MXU_SOURCE := src/mxu.zhl
SA_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuSystolicArray2x2Q16.sv
MXU_SEQ_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuMxuMicroSequencerD4.sv
MXU_FEEDER_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuMxuStreamFeeder4x4I8.sv
ZERO_SKIP_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuZeroSkipMask32.sv
STORAGE_SOURCE := src/storage.zhl
FIFO_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuStreamFifo32x4.sv
CQ_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuCompletionQueue8.sv
SCHEDULER_SOURCE := src/scheduler.zhl
CMDQ_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuCommandQueue4.sv
UB_SOURCE := src/ub.zhl
UB_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUnifiedBuffer256x32.sv
UB1024_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUnifiedBuffer1024x32.sv
UB_STREAM_SOURCE := src/ub_stream.zhl
UB_READER_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUbStreamReader32.sv
UB_WRITER_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUbStreamWriter32.sv
UB_MXU_FEEDER_SOURCE := src/ub_mxu_feeder.zhl
UB_MXU_FEEDER_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUbMxuFeeder4x4I8.sv
UB_MXU_COMPUTE_SOURCE := src/ub_mxu_compute.zhl
UB_MXU_COMPUTE_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUbMxuCompute2x2Q16.sv
UB_MXU_COMPUTE4_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUbMxuCompute4x4Q16.sv
UB_MXU_COMPUTE_I8_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUbMxuCompute4x4I8.sv
UB_DMA_SOURCE := src/ub_dma.zhl
UB_DMA_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUnifiedBufferDma64x32.sv
UB_DCOPY_SOURCE := src/ub_dcopy.zhl
UB_DCOPY_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUbDcopy64x32.sv
CMD_DMA_SOURCE := src/cmd_dma.zhl
CMD_DMA_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuCommandDescriptorDma64x24.sv
AXI_FENCE_SOURCE := src/axi_fence.zhl
AXI_READ_FENCE_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuAxiReadFence64x32.sv
AXI_WRITE_FENCE_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuAxiWriteFence64x32.sv
FAULT_STATUS_SOURCE := src/fault_status.zhl
FAULT_STATUS_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuDmaFenceFaultLatch64.sv
PERFMON_SOURCE := src/perfmon.zhl
PERFMON_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuPerfCounters32x8.sv
CFGBUS_SOURCE := src/cfgbus.zhl
CFGBUS_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuQueuedCfgAhb64x32.sv
CFGBUS_APB_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuQueuedCfgApb64x32.sv
FIXED_LUT_SOURCE := src/fixed_luts.zhl
RECIP_LUT_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuReciprocalSeedLutQ16.sv
RSQRT_LUT_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuRsqrtSeedLutQ16.sv
EXP_LUT_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuExpNegLutQ16.sv
LN_LUT_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuLnMantissaLutQ16.sv
FXP_MATH_SOURCE := src/fxp_math.zhl
RECIP_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuReciprocalNr2Q16.sv
RSQRT_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuRsqrtNr2Q16.sv
UB_VMU_SOURCE := src/ub_vmu.zhl
UB_VMU_ELEMENTWISE_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUbVmuElementwiseQ16.sv
UB_VMU_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUbVmuQ16.sv
UB_ADAM_SOURCE := src/ub_adam.zhl
UB_ADAM_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuUbAdamQ16.sv
QUEUED_Q16_SOURCE := src/queued_q16_slice.zhl
QUEUED_Q16_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuQueuedQ16Slice.sv
QUEUED_Q16_AHB_SOURCE := src/queued_q16_ahb_top.zhl
QUEUED_Q16_AHB_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuQueuedQ16AhbTop.sv
QUEUED_Q16_AHB4_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuQueuedQ16AhbTop4x4.sv
LAYOUT_DMA_CORE_SOURCE := src/layout_dma_core.zhl
LAYOUT_DMA_SOURCE := src/layout_dma.zhl
LAYOUT_DMA_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuLayoutDmaCopy64x32.sv
LAYOUT_DMA_AXI4_SOURCE := src/layout_dma_axi4.zhl
LAYOUT_DMA_AXI4_SYSTEMVERILOG := $(BUILD_DIR)/ZtpuLayoutDmaAxi4Master64x32.sv
LAYOUT_SOURCE := src/layout.zhl
TILER_SOURCE := src/tiler.zhl
LAYOUT_PATH_SOURCE := src/layout_path.zhl
AXI_ARBITER_SOURCE := src/axi_arbiter.zhl

.PHONY: check systemverilog sv-lint test formal simulator-diff q16-4x4-descriptor-replay tree-check release-audit release-check release-package clean

check:
	@command -v "$(ZLANGC)" >/dev/null 2>&1 || test -x "$(ZLANGC)" || { \
		echo "ZLang compiler not found: $(ZLANGC)" >&2; exit 2; \
	}
	@$(ZLANGC) $(PE_SOURCE) --project $(PROJECT) --check -v
	@$(ZLANGC) $(ARITH_SOURCE) --project $(PROJECT) --check -v
	@$(ZLANGC) $(MXU_SOURCE) --project $(PROJECT) --check -v
	@$(ZLANGC) $(STORAGE_SOURCE) --project $(PROJECT) --check -v
	@$(ZLANGC) $(SCHEDULER_SOURCE) --project $(PROJECT) --check -v
	@$(ZLANGC) $(UB_SOURCE) --project $(PROJECT) --top ZtpuUnifiedBuffer256x32 --check -v
	@$(ZLANGC) $(UB_SOURCE) --project $(PROJECT) --top ZtpuUnifiedBuffer1024x32 --check -v
	@$(ZLANGC) $(UB_STREAM_SOURCE) --project $(PROJECT) --top ZtpuUbStreamReader32 --check -v
	@$(ZLANGC) $(UB_STREAM_SOURCE) --project $(PROJECT) --top ZtpuUbStreamWriter32 --check -v
	@$(ZLANGC) $(UB_MXU_FEEDER_SOURCE) --project $(PROJECT) --top ZtpuUbMxuFeeder4x4I8 --check -v
	@$(ZLANGC) $(UB_MXU_COMPUTE_SOURCE) --project $(PROJECT) --top ZtpuUbMxuCompute2x2Q16 --check -v
	@$(ZLANGC) $(UB_MXU_COMPUTE_SOURCE) --project $(PROJECT) --top ZtpuUbMxuCompute4x4Q16 --check -v
	@$(ZLANGC) $(UB_MXU_COMPUTE_SOURCE) --project $(PROJECT) --top ZtpuUbMxuCompute4x4I8 --check -v
	@$(ZLANGC) $(UB_DMA_SOURCE) --project $(PROJECT) --top ZtpuUnifiedBufferDma64x32 --check -v
	@$(ZLANGC) $(UB_DCOPY_SOURCE) --project $(PROJECT) --top ZtpuUbDcopy64x32 --check -v
	@$(ZLANGC) $(CMD_DMA_SOURCE) --project $(PROJECT) --top ZtpuCommandDescriptorDma64x24 --check -v
	@$(ZLANGC) $(AXI_FENCE_SOURCE) --project $(PROJECT) --top ZtpuAxiReadFence64x32 --check -v
	@$(ZLANGC) $(AXI_FENCE_SOURCE) --project $(PROJECT) --top ZtpuAxiWriteFence64x32 --check -v
	@$(ZLANGC) $(FAULT_STATUS_SOURCE) --project $(PROJECT) --top ZtpuDmaFenceFaultLatch64 --check -v
	@$(ZLANGC) $(PERFMON_SOURCE) --project $(PROJECT) --top ZtpuPerfCounters32x8 --check -v
	@$(ZLANGC) $(CFGBUS_SOURCE) --project $(PROJECT) --top ZtpuQueuedCfgAhb64x32 --check -v
	@$(ZLANGC) $(CFGBUS_SOURCE) --project $(PROJECT) --top ZtpuQueuedCfgApb64x32 --check -v
	@$(ZLANGC) $(FIXED_LUT_SOURCE) --project $(PROJECT) --top ZtpuReciprocalSeedLutQ16 --check -v
	@$(ZLANGC) $(FIXED_LUT_SOURCE) --project $(PROJECT) --top ZtpuRsqrtSeedLutQ16 --check -v
	@$(ZLANGC) $(FIXED_LUT_SOURCE) --project $(PROJECT) --top ZtpuExpNegLutQ16 --check -v
	@$(ZLANGC) $(FIXED_LUT_SOURCE) --project $(PROJECT) --top ZtpuLnMantissaLutQ16 --check -v
	@$(ZLANGC) $(FXP_MATH_SOURCE) --project $(PROJECT) --top ZtpuReciprocalNr2Q16 --check -v
	@$(ZLANGC) $(FXP_MATH_SOURCE) --project $(PROJECT) --top ZtpuRsqrtNr2Q16 --check -v
	@$(ZLANGC) $(UB_VMU_SOURCE) --project $(PROJECT) --top ZtpuUbVmuElementwiseQ16 --check -v
	@$(ZLANGC) $(UB_VMU_SOURCE) --project $(PROJECT) --top ZtpuUbVmuQ16 --check -v
	@$(ZLANGC) $(UB_ADAM_SOURCE) --project $(PROJECT) --top ZtpuUbAdamQ16 --check -v
	@$(ZLANGC) $(QUEUED_Q16_SOURCE) --project $(PROJECT) --top ZtpuQueuedQ16Slice --check -v
	@$(ZLANGC) $(QUEUED_Q16_AHB_SOURCE) --project $(PROJECT) --top ZtpuQueuedQ16AhbTop --check -v
	@$(ZLANGC) $(QUEUED_Q16_AHB_SOURCE) --project $(PROJECT) --top ZtpuQueuedQ16AhbTop4x4 --check -v
	@$(ZLANGC) $(LAYOUT_DMA_CORE_SOURCE) --project $(PROJECT) --top ZtpuLayoutDmaControl64x32 --check -v
	@$(ZLANGC) $(LAYOUT_DMA_SOURCE) --project $(PROJECT) --top ZtpuLayoutDmaCopy64x32 --check -v
	@$(ZLANGC) $(LAYOUT_DMA_AXI4_SOURCE) --project $(PROJECT) --top ZtpuLayoutDmaAxi4Master64x32 --check -v
	@$(ZLANGC) $(LAYOUT_SOURCE) --project $(PROJECT) --top ZtpuLayoutTranspose64 --check -v
	@$(ZLANGC) $(TILER_SOURCE) --project $(PROJECT) --top ZtpuTiler64x256 --check -v
	@$(ZLANGC) $(LAYOUT_PATH_SOURCE) --project $(PROJECT) --top ZtpuLayoutPath64x32 --check -v
	@$(ZLANGC) $(AXI_ARBITER_SOURCE) --project $(PROJECT) --top ZtpuAxiReadArbiter2x64x32 --check -v
	@$(ZLANGC) $(AXI_ARBITER_SOURCE) --project $(PROJECT) --top ZtpuAxiWriteArbiter2x64x32 --check -v

systemverilog: check
	@mkdir -p $(BUILD_DIR)
	@$(ZLANGC) $(PE_SOURCE) --project $(PROJECT) --top ZtpuPeQ16 \
		--systemverilog $(PE_SYSTEMVERILOG) -v
	@$(ZLANGC) $(ARITH_SOURCE) --project $(PROJECT) --top ZtpuActivationQ16x4 \
		--systemverilog $(ACTIVATION_SYSTEMVERILOG) -v
	@$(ZLANGC) $(ARITH_SOURCE) --project $(PROJECT) --top ZtpuBiasAccumulateQ16x4 \
		--systemverilog $(BAU_SYSTEMVERILOG) -v
	@$(ZLANGC) $(ARITH_SOURCE) --project $(PROJECT) --top ZtpuAccRequant8 \
		--systemverilog $(RQ8_SYSTEMVERILOG) -v
	@$(ZLANGC) $(ARITH_SOURCE) --project $(PROJECT) --top ZtpuAccRequant16 \
		--systemverilog $(RQ16_SYSTEMVERILOG) -v
	@$(ZLANGC) $(ARITH_SOURCE) --project $(PROJECT) --top ZtpuAccRequant32 \
		--systemverilog $(RQ32_SYSTEMVERILOG) -v
	@$(ZLANGC) $(MXU_SOURCE) --project $(PROJECT) --top ZtpuSystolicArray2x2Q16 \
		--systemverilog $(SA_SYSTEMVERILOG) -v
	@$(ZLANGC) $(MXU_SOURCE) --project $(PROJECT) --top ZtpuMxuMicroSequencerD4 \
		--systemverilog $(MXU_SEQ_SYSTEMVERILOG) -v
	@$(ZLANGC) $(MXU_SOURCE) --project $(PROJECT) --top ZtpuMxuStreamFeeder4x4I8 \
		--systemverilog $(MXU_FEEDER_SYSTEMVERILOG) -v
	@$(ZLANGC) $(MXU_SOURCE) --project $(PROJECT) --top ZtpuZeroSkipMask32 \
		--systemverilog $(ZERO_SKIP_SYSTEMVERILOG) -v
	@$(ZLANGC) $(STORAGE_SOURCE) --project $(PROJECT) --top ZtpuStreamFifo32x4 \
		--systemverilog $(FIFO_SYSTEMVERILOG) -v
	@$(ZLANGC) $(STORAGE_SOURCE) --project $(PROJECT) --top ZtpuCompletionQueue8 \
		--systemverilog $(CQ_SYSTEMVERILOG) -v
	@$(ZLANGC) $(SCHEDULER_SOURCE) --project $(PROJECT) --top ZtpuCommandQueue4 \
		--systemverilog $(CMDQ_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_SOURCE) --project $(PROJECT) --top ZtpuUnifiedBuffer256x32 \
		--systemverilog $(UB_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_SOURCE) --project $(PROJECT) --top ZtpuUnifiedBuffer1024x32 \
		--systemverilog $(UB1024_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_STREAM_SOURCE) --project $(PROJECT) --top ZtpuUbStreamReader32 \
		--systemverilog $(UB_READER_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_STREAM_SOURCE) --project $(PROJECT) --top ZtpuUbStreamWriter32 \
		--systemverilog $(UB_WRITER_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_MXU_FEEDER_SOURCE) --project $(PROJECT) --top ZtpuUbMxuFeeder4x4I8 \
		--systemverilog $(UB_MXU_FEEDER_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_MXU_COMPUTE_SOURCE) --project $(PROJECT) --top ZtpuUbMxuCompute2x2Q16 \
		--systemverilog $(UB_MXU_COMPUTE_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_MXU_COMPUTE_SOURCE) --project $(PROJECT) --top ZtpuUbMxuCompute4x4Q16 \
		--systemverilog $(UB_MXU_COMPUTE4_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_MXU_COMPUTE_SOURCE) --project $(PROJECT) --top ZtpuUbMxuCompute4x4I8 \
		--systemverilog $(UB_MXU_COMPUTE_I8_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_DMA_SOURCE) --project $(PROJECT) --top ZtpuUnifiedBufferDma64x32 \
		--systemverilog $(UB_DMA_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_DCOPY_SOURCE) --project $(PROJECT) --top ZtpuUbDcopy64x32 \
		--systemverilog $(UB_DCOPY_SYSTEMVERILOG) -v
	@$(ZLANGC) $(CMD_DMA_SOURCE) --project $(PROJECT) --top ZtpuCommandDescriptorDma64x24 \
		--systemverilog $(CMD_DMA_SYSTEMVERILOG) -v
	@$(ZLANGC) $(AXI_FENCE_SOURCE) --project $(PROJECT) --top ZtpuAxiReadFence64x32 \
		--systemverilog $(AXI_READ_FENCE_SYSTEMVERILOG) -v
	@$(ZLANGC) $(AXI_FENCE_SOURCE) --project $(PROJECT) --top ZtpuAxiWriteFence64x32 \
		--systemverilog $(AXI_WRITE_FENCE_SYSTEMVERILOG) -v
	@$(ZLANGC) $(FAULT_STATUS_SOURCE) --project $(PROJECT) --top ZtpuDmaFenceFaultLatch64 \
		--systemverilog $(FAULT_STATUS_SYSTEMVERILOG) -v
	@$(ZLANGC) $(PERFMON_SOURCE) --project $(PROJECT) --top ZtpuPerfCounters32x8 \
		--systemverilog $(PERFMON_SYSTEMVERILOG) -v
	@$(ZLANGC) $(CFGBUS_SOURCE) --project $(PROJECT) --top ZtpuQueuedCfgAhb64x32 \
		--systemverilog $(CFGBUS_SYSTEMVERILOG) -v
	@$(ZLANGC) $(CFGBUS_SOURCE) --project $(PROJECT) --top ZtpuQueuedCfgApb64x32 \
		--systemverilog $(CFGBUS_APB_SYSTEMVERILOG) -v
	@$(ZLANGC) $(FIXED_LUT_SOURCE) --project $(PROJECT) --top ZtpuReciprocalSeedLutQ16 \
		--systemverilog $(RECIP_LUT_SYSTEMVERILOG) -v
	@$(ZLANGC) $(FIXED_LUT_SOURCE) --project $(PROJECT) --top ZtpuRsqrtSeedLutQ16 \
		--systemverilog $(RSQRT_LUT_SYSTEMVERILOG) -v
	@$(ZLANGC) $(FIXED_LUT_SOURCE) --project $(PROJECT) --top ZtpuExpNegLutQ16 \
		--systemverilog $(EXP_LUT_SYSTEMVERILOG) -v
	@$(ZLANGC) $(FIXED_LUT_SOURCE) --project $(PROJECT) --top ZtpuLnMantissaLutQ16 \
		--systemverilog $(LN_LUT_SYSTEMVERILOG) -v
	@$(ZLANGC) $(FXP_MATH_SOURCE) --project $(PROJECT) --top ZtpuReciprocalNr2Q16 \
		--systemverilog $(RECIP_SYSTEMVERILOG) -v
	@$(ZLANGC) $(FXP_MATH_SOURCE) --project $(PROJECT) --top ZtpuRsqrtNr2Q16 \
		--systemverilog $(RSQRT_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_VMU_SOURCE) --project $(PROJECT) --top ZtpuUbVmuElementwiseQ16 \
		--systemverilog $(UB_VMU_ELEMENTWISE_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_VMU_SOURCE) --project $(PROJECT) --top ZtpuUbVmuQ16 \
		--systemverilog $(UB_VMU_SYSTEMVERILOG) -v
	@$(ZLANGC) $(UB_ADAM_SOURCE) --project $(PROJECT) --top ZtpuUbAdamQ16 \
		--systemverilog $(UB_ADAM_SYSTEMVERILOG) -v
	@$(ZLANGC) $(QUEUED_Q16_SOURCE) --project $(PROJECT) --top ZtpuQueuedQ16Slice \
		--systemverilog $(QUEUED_Q16_SYSTEMVERILOG) -v
	@$(ZLANGC) $(QUEUED_Q16_AHB_SOURCE) --project $(PROJECT) --top ZtpuQueuedQ16AhbTop \
		--systemverilog $(QUEUED_Q16_AHB_SYSTEMVERILOG) -v
	@$(ZLANGC) $(QUEUED_Q16_AHB_SOURCE) --project $(PROJECT) --top ZtpuQueuedQ16AhbTop4x4 \
		--systemverilog $(QUEUED_Q16_AHB4_SYSTEMVERILOG) -v
	@$(ZLANGC) $(LAYOUT_DMA_SOURCE) --project $(PROJECT) --top ZtpuLayoutDmaCopy64x32 \
		--systemverilog $(LAYOUT_DMA_SYSTEMVERILOG) -v
	@$(ZLANGC) $(LAYOUT_DMA_AXI4_SOURCE) --project $(PROJECT) --top ZtpuLayoutDmaAxi4Master64x32 \
		--systemverilog $(LAYOUT_DMA_AXI4_SYSTEMVERILOG) -v

sv-lint: systemverilog
	@$(VERILATOR) --lint-only -Wall --top-module ZtpuPeQ16 $(PE_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall --top-module ZtpuActivationQ16x4 $(ACTIVATION_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall --top-module ZtpuBiasAccumulateQ16x4 $(BAU_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuAccRequant8 $(RQ8_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuAccRequant16 $(RQ16_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuAccRequant32 $(RQ32_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuSystolicArray2x2Q16 $(SA_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuMxuMicroSequencerD4 $(MXU_SEQ_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall \
		--top-module ZtpuMxuStreamFeeder4x4I8 $(MXU_FEEDER_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall \
		--top-module ZtpuZeroSkipMask32 $(ZERO_SKIP_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall \
		--top-module ZtpuStreamFifo32x4 $(FIFO_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall \
		--top-module ZtpuCompletionQueue8 $(CQ_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-UNUSEDSIGNAL \
		--top-module ZtpuCommandQueue4 $(CMDQ_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUnifiedBuffer256x32 $(UB_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUnifiedBuffer1024x32 $(UB1024_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUbStreamReader32 $(UB_READER_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUbStreamWriter32 $(UB_WRITER_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUbMxuFeeder4x4I8 $(UB_MXU_FEEDER_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUbMxuCompute2x2Q16 $(UB_MXU_COMPUTE_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUbMxuCompute4x4Q16 $(UB_MXU_COMPUTE4_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUbMxuCompute4x4I8 $(UB_MXU_COMPUTE_I8_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUnifiedBufferDma64x32 $(UB_DMA_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUbDcopy64x32 $(UB_DCOPY_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuCommandDescriptorDma64x24 $(CMD_DMA_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuAxiReadFence64x32 $(AXI_READ_FENCE_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuAxiWriteFence64x32 $(AXI_WRITE_FENCE_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuDmaFenceFaultLatch64 $(FAULT_STATUS_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuPerfCounters32x8 $(PERFMON_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuQueuedCfgAhb64x32 $(CFGBUS_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuQueuedCfgApb64x32 $(CFGBUS_APB_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuReciprocalSeedLutQ16 $(RECIP_LUT_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuRsqrtSeedLutQ16 $(RSQRT_LUT_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuExpNegLutQ16 $(EXP_LUT_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuLnMantissaLutQ16 $(LN_LUT_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuReciprocalNr2Q16 $(RECIP_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuRsqrtNr2Q16 $(RSQRT_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUbVmuElementwiseQ16 $(UB_VMU_ELEMENTWISE_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUbVmuQ16 $(UB_VMU_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuUbAdamQ16 $(UB_ADAM_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuQueuedQ16Slice $(QUEUED_Q16_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuQueuedQ16AhbTop $(QUEUED_Q16_AHB_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuQueuedQ16AhbTop4x4 $(QUEUED_Q16_AHB4_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuLayoutDmaCopy64x32 $(LAYOUT_DMA_SYSTEMVERILOG)
	@$(VERILATOR) --lint-only -Wall -Wno-DECLFILENAME -Wno-UNUSEDSIGNAL \
		--top-module ZtpuLayoutDmaAxi4Master64x32 $(LAYOUT_DMA_AXI4_SYSTEMVERILOG)

test: sv-lint
	@ZLANGC="$(ZLANGC)" $(PYTHON) -m pytest -q \
		tests/test_pe.py tests/test_arithmetic.py \
		tests/test_mxu.py tests/test_storage.py \
		tests/test_scheduler.py \
		tests/test_ub.py \
		tests/test_ub_stream.py \
		tests/test_ub_mxu_feeder.py \
		tests/test_ub_mxu_compute.py \
		tests/test_ub_mxu_compute_i8.py \
		tests/test_ub_dma.py \
		tests/test_ub_dcopy.py \
		tests/test_cmd_dma.py \
		tests/test_axi_fence.py \
		tests/test_fault_status.py \
		tests/test_perfmon.py \
		tests/test_cfgbus.py \
		tests/test_cfgbus_frontends.py \
		tests/test_fixed_luts.py \
		tests/test_ub_vmu.py \
		tests/test_ub_adam.py \
		tests/test_queued_q16_slice.py \
		tests/test_queued_q16_ahb_top.py \
		tests/test_queued_q16_ahb_top_4x4.py \
		tests/test_axi_arbiter.py \
		tests/test_layout_dma.py \
		tests/test_simulator_diff.py \
		tests/test_tree_policy.py

formal:
	@$(PYTHON) tools/formal_verify.py --zlang "$(ZLANGC)"

simulator-diff:
	@PYTHONDONTWRITEBYTECODE=1 $(PYTHON) tools/simulator_diff.py

q16-4x4-descriptor-replay:
	@ZLANGC="$(ZLANGC)" $(PYTHON) -m pytest -q \
		tests/test_ub_mxu_compute.py tests/test_queued_q16_ahb_top_4x4.py

tree-check:
	@$(PYTHON) tools/check_tree.py

release-audit: tree-check
	@$(PYTHON) tools/release_check.py

release-check: test formal simulator-diff tree-check
	@git diff --check
	@$(PYTHON) tools/release_check.py --require-single-commit --require-clean

release-package: release-check
	@$(PYTHON) tools/build_release_archive.py

clean:
	@rm -rf $(BUILD_DIR) .pytest_cache tests/__pycache__ tools/__pycache__
