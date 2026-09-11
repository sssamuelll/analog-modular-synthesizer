--- jake-taf 2026-03-10T13:13:30Z
Seems resolved on the latest build, but we'll see

--- jake-taf 2026-05-14T16:47:05Z
Not resolved, just less likely it seems (anywhere from several minutes to two hours from testing)

Writing to the TXDR (transmit data register) allows it to recover from this frozen state). So I can have a high-priority interrupt executor recover it if it freezes by writing that, but this shouldn't be happening in the first place.

--- jake-taf 2026-05-15T14:02:21Z
Asynchronous SPI with DMA has the same issue. Writing to the transmit buffer does not recover, but DMA may work a bit differently. It gets stuck in the finish_dma function waiting for the end of transfer flag.

I wonder if my use of interrupts upsets it somehow? Maybe some bug if the SPI transfer is interrupted at the right moment.

--- stefkoriz 2026-05-21T15:26:46Z
Hi Jake-taf I have same issue with my SDK I connected fast 16 bit ADC on SPI5 port. Seems that this is the issue with silicon running SPI on high frequency. SPI freeze and not send any data after 1-2 sec. RXP flag is not set and SR show when work 0x301A, when stop work SR show 0x12017 or similar and CR1 show CR1=0x0201. Exit from this only to restart SPI engine. I run SPI transfer inside the Timer ISR routine. where sampling ADC with 352KHz sampling rate  
Did you have any idea or solution 

--- jake-taf 2026-05-26T14:38:33Z
@stefkoriz Unfortunately not. Right now my solution is to detect when SPI stalls (I have a high-priority interrupt task that can check timestamps in a mutex) and send more bits (`PI1.txdr8().write_value(0)`) to get out of stall. The value that's read will need to be discarded.

For me it seems to happen every 30-120 minutes regardless of how often I write/read to SPI. This is not ideal of course. I need to investigate further, but I'm fairly new to this stuff.

--- jake-taf 2026-05-26T14:45:28Z
@xoviat Hmm, I wonder how the N6 C HAL compares to what we currently do? If it's different maybe following that will lead to better results. I didn't see anyone complaining about it when using the C HAL at least. I'll check that out

--- xoviat 2026-05-26T14:49:45Z
See here:

https://github.com/STMicroelectronics/stm32n6xx-hal-driver/blob/0a07a27bcef917fa584335212cb8e031ccfbfc8c/Src/stm32n6xx_hal_spi.c#L1072

--- xoviat 2026-05-26T15:02:48Z
Note: I removed my comment about EOT because the blocking read does not actually check EOT, it checks RXP like we do. Some differences that I see: 
- the ST code sets tsize
- the ST code does not read/write to the tx registers, I think?

--- xoviat 2026-05-29T20:36:28Z
@jake-taf does https://github.com/embassy-rs/embassy/commit/f7d6e412d1104925e542ddac7159d5874db2c3b5 hang?

--- jake-taf 2026-05-29T20:54:45Z
I'll take a look. The downside of it only happening sometimes is it's hard to know if it's definitely gone, but I'll run something overnight and see

--- stefkoriz 2026-06-01T15:15:22Z
to keep consistency of the ADC data stream I repeated last valid data until get new valid data ( restarting SPI engine)  this make 6 sequential data with same value stored in the file. I think that this happens on specific number of SPI transfers after that SPI frozen. My record is 30sec = 24Mbytes  and have  5-6 SPI restarts. 
Monitoring EOT and RXP flags in same time help to decide when is time to restart SPI.

--- jake-taf 2026-06-11T21:05:13Z
@xoviat Apologies for the delays. I'm running a test now and will let you know. I also noticed the SPI bits will occasionally (once or twice a minute) be corrupted. I only noticed when enabling CRC on a chip I was talking to over SPI. 

# A normal read

1. Grey = chip select
2. Red = SCLK

<img width="1042" height="982" alt="Image" src="https://github.com/user-attachments/assets/caa4ebe4-ed35-4682-9b9a-2264a55805e1" />

# A corrupted read (CRC fails)

Notice the chip select goes high before we're done clocking data. The software sees this as the bits being shifted half way through. I can't help but wonder if the stall is a special case of this, since it seems to happen when we fail to send or receive all the bits, which makes sense if we are somehow ending the transaction early

<img width="1351" height="680" alt="Image" src="https://github.com/user-attachments/assets/fc2e8bb6-11e5-4937-ac35-274c36659d2c" />

**Zoomed in on another corrupted message**

<img width="1042" height="982" alt="Image" src="https://github.com/user-attachments/assets/13927f17-c685-47e6-83b5-652fe7eca3e2" />

--- jake-taf 2026-06-11T22:52:48Z
Maybe this isn't it, but I notice in the [embassy SPI driver](https://github.com/embassy-rs/embassy/blob/main/embassy-stm32/src/spi/mod.rs) that blocking write waits until the TXC flag is set (TxFIFO is empty and there's no activity on the bus). But reads don't wait for anything. They return as soon as the transfer function is done.

Maybe that's why it's only reads that seem broken? The read is returning because data is in the FIFO, not because it's complete, and then the driver releases the CS too early?

https://github.com/embassy-rs/embassy/blob/9e31679810ce57f10d0466fbe62afd3502d98357/embassy-stm32/src/spi/mod.rs#L591-L595

Although if that were the case, I don't understand why DMA SPI would get stuck waiting for `EOT` in `finish_dma`?

--- xoviat 2026-06-11T23:13:43Z
> They return as soon as the transfer function is done.

Yes, because if you've received as many words as you've sent, then the assumption is that the bus is idle. I'm not sure how this assumption can be invalidated.

--- xoviat 2026-06-11T23:16:44Z
I mean, you can make any changes you want to the code and submit them. If it fixes the problem, then obviously it means there's an issue with the current implementation. 

>  I also noticed the SPI bits will occasionally (once or twice a minute) be corrupted

Which revision had this issue?

--- jake-taf 2026-06-12T07:01:45Z
Perhaps I misunderstood that then (since it doesn't fully explain DMA having the same issue), but yeah, I can play around to see if I can resolve it.

This is 24e5731acec720a64360294cfafadcd771701c71, but with the PAC `stm32-data-505dc9dcc8ab28102d3ea12f3cafd387e7f767e4` (added back the N6 timers) instead of `stm32-data-7aaa9af0001abcfb01c01e1a9b048697a82b7d57`. I do recall having this issue a few months ago, when doing tests on the discovery kit, so it's not a new problem for N6 SPI

--- xoviat 2026-06-16T01:57:35Z
This is the claude-generated fix. Does this work?

```
    // ... existing code ...
    transfer_words(self.info.regs, words, &[])?;
    
    // Wait until transfer is actually complete before returning
    #[cfg(not(any(spi_v1, spi_v2, spi_v3)))]
    while !self.info.regs.sr().read().txc() {}
    #[cfg(spi_v3)]
    while self.info.regs.sr().read().bsy() {}
```

--- xoviat 2026-06-16T02:11:34Z
claude: 

> You're absolutely right to question that. In standard full-duplex SPI, when you've written N bytes and read N bytes, the bus should be idle — there's no way to have unclocked bits still in flight.
> 
> However, looking at the STM32 spi_v4+ architecture, there's a subtlety: the RXP flag doesn't necessarily mean the data has been shifted out to the bus — it means data is available in the RX FIFO.
> 
> The sequence is:
> 
> Write byte to TX FIFO
> Hardware shifts it out and receives simultaneously
> Received byte goes into RX FIFO
> RXP flag sets when FIFO has data
> Software reads from RX FIFO
> The problem is that between steps 3-4, there can be a delay. Or more importantly, the hardware might have the last bit still being clocked when the RXP flag is checked.
> 
> But actually, you're pointing out a deeper issue with my explanation. Let me reconsider: if transfer_words waits until r >= ndt, meaning all N bytes have been read from the RX FIFO, then by definition those bytes were shifted in, which means the corresponding bytes were shifted out.
> 
> So the real question is: why would transfer_words return with valid data in the RX FIFO, but the bus isn't actually idle?
> 
> Looking at Jake's comment again about the oscilloscope trace — CS goes high mid-transfer. This suggests either:
> 
> transfer_words is returning early somehow before all data is actually exchanged
> CS is being controlled externally (by your application) and is toggling while the SPI is still active
> There's a hardware state machine issue on the N6 where the SPI thinks it's done but the bus activity continues
> Is the CS pin in your test code manually controlled by your application? That would explain why it could go high before the SPI is actually done.

--- jake-taf 2026-06-16T13:20:43Z
I'll give it a shot!

--- jake-taf 2026-06-17T08:49:43Z
@xoviat Nope, that didn't fix it. You can see my modified code here.

https://github.com/turnaroundfactor/embassy/blob/05e7b99062eb07c4de6b13850401648dc49af0d6/embassy-stm32/src/spi/mod.rs#L614-L619

**Flag docs**

<img width="1172" height="334" alt="Image" src="https://github.com/user-attachments/assets/bf4b3017-547b-45dc-8dc6-81f2238665aa" />

<img width="1142" height="449" alt="Image" src="https://github.com/user-attachments/assets/05505a6f-26e0-449b-a684-ddd1537e6602" />

--- jake-taf 2026-06-17T09:21:26Z
And it just gets worse :(

I saw the SPI lockup again, so that's not resolved

--- jake-taf 2026-06-17T09:57:25Z
How does this theory sound?

SPI reads are occasionally duplicating a data bit and thus shifting the data 1-bit to the right. This results in the SPI terminating early (e.g. it thinks it got all 8-bits, when it only got 7-bits), which then causes the CS to raise early. 

I should think SCLK would also stop, but maybe it can only clock in multiples of eight?

Here's an example with real data where you can see a zero get duplicated. This happens on the disco kit, and the freeze (if it's the same issue) happens even when nothing's connected.

```diff
Normal
- 11100111 01001011 00010001 00100010 00001000 00000101 01100011 01100101 01110011 00100000 01101000 01100001 01110110
Corrupted
+ 11100111 01001011 00010001 00100010 00001000 00000010 10110001 10110010 10111001 10010000 00110100 00110000 10111011
                                               ^
                                               ^
                                               ^
                                        Bit duplicated
```

But I don't understand why that would happen since the capture looks pretty clean. I tried different SPI speeds and it doesn't seem to matter (captures were for 100kHz)

**Normal**

<img width="1832" height="708" alt="Image" src="https://github.com/user-attachments/assets/7f4a5a99-3863-472b-a3b3-1ee9a8a431b6" />

**Corrupted**

<img width="1832" height="708" alt="Image" src="https://github.com/user-attachments/assets/31640597-130c-4459-b2ef-a668f3588e8e" />



--- jake-taf 2026-06-17T10:19:05Z
It's hard to know if that's a symptom of the CS going high early, or if CS going high early is a symptom of this. Ugh 🫠

--- jake-taf 2026-06-17T12:53:34Z
I don't think it's interrupt related, as I wrapped my SPI call in a `critical_section::with` and it didn't help

--- jake-taf 2026-06-17T13:45:43Z
I don't think it'd be `tsize` either, since we see the freeze with the DMA SPI code too. I haven't checked if the chip select issue happens for DMA, but it probably does?

--- jake-taf 2026-06-24T12:41:29Z
I'll try running this with the C code to confirm it's only happening on embassy

--- sssamuelll 2026-09-03T12:24:57Z
A few observations from reading this thread against RM0486 Rev 4 (STM32N6 reference manual) and the current `spi/mod.rs`, in case they help narrow it down:

**1. Both reports here are on `SPI5`.** @jake-taf @stefkoriz — has either of you reproduced this on a different SPI instance? I'm designing around six independent links on `SPI1`–`SPI6` on an N657, and whether this is instance-specific or block-wide changes the recovery strategy quite a bit. If nobody has tried, it seems like the cheapest next experiment on the DK.

**2. The two repros terminate the transfer differently.** The blocking path (`blocking_read` → `transfer_word`; the register dump in the OP shows `TSIZE = 0`, `CSTART = 1`, `TXC = 1`, `RXP = 0`) and DMA `write`/`transfer` run as an *endless* transfer (`TSIZE = 0`) and wait on `TXC`; DMA `read` is the only path that sets `TSIZE` and waits on `EOT`. Since the DMA hang was reported "waiting for the end of transfer flag", that one was presumably in `read` with `TSIZE > 0` — so `TSIZE` alone doesn't seem to be the discriminator. Still, the RM is explicit that the two terminations are different state-machine paths, e.g. §67.4.13, p. 3449:

> *"When TSIZE > 0, EOT and TXC signals are equal so polling of EOT is reliable at whatever SPI communication mode to check the end of the bus activity. When TSIZE = 0, the user has to check TXC, SUSP, or FIFO occupancy flags according to the applied SPI mode and the way of the data flow termination."*

**3. One RM detail worth checking on the `read` path.** §67.11.6, p. 3492, on the `EOT` bit:

> *"EOT is set by hardware as soon as a full transfer is complete, that is when SPI is re-enabled or when TSIZE number of data have been transmitted and/or received on the SPI. EOT is cleared when SPI is re-enabled or by writing 1 to the EOTC bit of the SPI_IFCR register optionally."*

The driver re-enables `SPE` right before `CSTART` on every transfer and doesn't write `EOTC` afterwards. If the "set when SPI is re-enabled" clause is what the silicon does, `finish_dma` could be reading a stale `EOT` on some iterations — which would look like a transfer that "completes" before the bus is idle. That's a hypothesis, not a diagnosis; I haven't got hardware to test it yet.

**4. Hardware NSS.** Both repros drive CS from a GPIO (`SSM = 1` in the dump). The RM ties hardware NSS to `TSIZE > 0` (§67.4.7, p. 3437: *"the master must apply the proper TSIZE > 0 setting to control the NSS output correctly"*). Has anyone seen the hang with `SSM = 0, SSOE = 1`? That's the mode I'll be using, so I'd be interested either way.

Also: was the comparison against the C HAL (mentioned 2026-06-24) ever run? That would settle silicon-vs-driver, and I couldn't find the result in the thread.

Happy to run a long soak on a DK across instances with hardware NSS once I have one; I'll report back here either way.


--- jake-taf 2026-09-03T13:09:13Z
1. I have observed this problem on SPI1 as well
2. Interesting. I stuck with blocking since I have a workaround when it gets stuck (`SPI1.txdr8().write_value(0)`), but both have the problem
4. I haven't tried that mode. We wrote some small test firmware for C, but had issues getting probe-rs working on C. I'll update the thread if we do get that functional!

Thanks for the help! Something funky is going on and it'd be great to figure it out

