#!/usr/bin/rscript --vanilla

rm(list=ls())



dui.frame <- read.table("duistats☎.tsv", stringsAsFactors=FALSE, 
                        sep='\t', header=TRUE)

teen.frame <- read.csv("teenstats.csv", stringsAsFactors=FALSE)


# dui frame to upper
dui.frame$State <- toupper(dui.frame$State)
dui.frame[9,1] <- "D.C."

# control for population size (the higher, the worse)
dui.frame$dui.score <- dui.frame$DUI.Arrests..2012. / dui.frame$Population.Size

# rank states by fewest dui arrests by population
dui.frame <- dui.frame[ order(dui.frame$dui.score), ]
dui.frame$rank <- 1:nrow(dui.frame)

names(teen.frame)[1] <- "State"
names(teen.frame)[2] <- "Percent.HS.Grad"
test <- merge(dui.frame, teen.frame[,c(1,2)])

plot(test$dui.score ~ test$Percent.HS.Grad)
dev.copy(png,'correlation.png')
dev.off()

res <- lm(test$dui.score ~ test$Percent.HS.Grad)

write(res$coefficients, "lmcoeffs.txt")

